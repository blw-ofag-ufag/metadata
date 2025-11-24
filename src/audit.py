import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

import aiohttp
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session, sessionmaker

# Local modules
from src.config import settings
from src.models import (
    Base, Dataset, Distribution, QualityViolation, 
    DatasetInput, DistributionInput
)
from src.logic import QualityScorer

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# HTTP Status Codes for Internal Handling
HTTP_TIMEOUT = 408
HTTP_SSL_ERROR = 495
HTTP_CONNECTION_ERROR = 503
HTTP_OTHER_ERROR = 400

class AsyncUrlChecker:
    """
    Handles asynchronous URL validation with concurrency control and User-Agent injection.
    """
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.ASYNC_PER_DOMAIN)
        self.headers = {"User-Agent": settings.USER_AGENT}
        # Cache for results to avoid checking same URL multiple times in one run
        self._results_cache: Dict[str, int] = {}

    async def check_distributions(self, distributions: List[DistributionInput]):
        """
        Orchestrates checking a list of distributions. Updates them in-place.
        """
        tasks = []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for dist in distributions:
                # Check Access URL
                # FIX: Changed "access" to "access_url" to match model field "access_url_status"
                if dist.access_url and self.should_check(dist, "access_url"):
                    tasks.append(self._audit_url(dist, "access_url", session))
                
                # Check Download URL
                # FIX: Changed "download" to "download_url" to match model field "download_url_status"
                if dist.download_url and self.should_check(dist, "download_url"):
                    tasks.append(self._audit_url(dist, "download_url", session))
            
            if tasks:
                logger.info(f"Auditing {len(tasks)} URLs asynchronously...")
                await asyncio.gather(*tasks)

    def should_check(self, dist: DistributionInput, url_type: str) -> bool:
        """
        Determines if a URL needs re-checking.
        Logic:
        1. If status is currently None (New record or never checked).
        2. If URL changed (Logic handled in pipeline upsert).
        """
        # This constructs "access_url_status" or "download_url_status"
        current_status = getattr(dist, f"{url_type}_status")
        
        # If we have no status, we must check
        if current_status is None:
            return True
            
        return False

    async def _audit_url(self, dist: DistributionInput, field_name: str, session: aiohttp.ClientSession):
        # field_name is "access_url" or "download_url". 
        # We get the URL string directly.
        url = getattr(dist, field_name) 
        
        if not url:
            return

        if url in self._results_cache:
            status = self._results_cache[url]
        else:
            async with self.semaphore:
                status = await self._fetch_status(url, session)
                self._results_cache[url] = status
        
        # Update the Pydantic model in-place. 
        # We construct "access_url_status" here.
        setattr(dist, f"{field_name}_status", status)

    async def _fetch_status(self, url: str, session: aiohttp.ClientSession) -> int:
        try:
            async with session.head(url, timeout=10, allow_redirects=True) as response:
                return response.status
        except asyncio.TimeoutError:
            return HTTP_TIMEOUT
        except aiohttp.ClientSSLError:
            return HTTP_SSL_ERROR
        except aiohttp.ClientConnectionError:
            return HTTP_CONNECTION_ERROR
        except Exception as e:
            return HTTP_OTHER_ERROR


class AuditPipeline:
    def __init__(self):
        self.engine = create_engine(settings.DB_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.checker = AsyncUrlChecker()
        self.scorer = QualityScorer()

    def init_db(self):
        """Ensure tables exist."""
        Base.metadata.create_all(self.engine)

    def load_raw_data(self) -> List[DatasetInput]:
        """Load and parse the JSON source of truth."""
        if not settings.RAW_DATA_FILE.exists():
            logger.error(f"Raw data file not found: {settings.RAW_DATA_FILE}")
            sys.exit(1)
            
        with open(settings.RAW_DATA_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        logger.info(f"Loaded {len(raw_data)} records from JSON.")
        return [DatasetInput(**d) for d in raw_data]

    def prune_records(self, session: Session, input_ids: Set[str]):
        """Step 1: Delete DB records that are no longer in the input."""
        stmt = select(Dataset.id)
        existing_ids = set(session.scalars(stmt).all())
        
        to_delete = existing_ids - input_ids
        if to_delete:
            logger.info(f"Pruning {len(to_delete)} obsolete datasets from DB.")
            session.execute(delete(Dataset).where(Dataset.id.in_(to_delete)))
            session.commit()

    def hydrate_and_sync(self, session: Session, inputs: List[DatasetInput]):
        """
        Step 2: Merge Input data with DB data.
        If URL hasn't changed, preserve the old HTTP status from DB to avoid re-checking.
        """
        # Pre-fetch existing distributions to map URLs -> Status
        existing_dists_query = select(Distribution)
        db_dists = session.scalars(existing_dists_query).all()
        
        # Map: (dataset_id, distribution_identifier) -> DistributionORM
        db_dist_map = {
            (d.dataset_id, d.identifier): d 
            for d in db_dists if d.identifier
        }

        count_preserved = 0
        
        for ds_input in inputs:
            for dist_input in ds_input.distributions:
                key = (ds_input.id, dist_input.identifier)
                
                if key in db_dist_map:
                    db_dist = db_dist_map[key]
                    
                    # Preserve Access URL Status if URL is unchanged
                    if db_dist.access_url == dist_input.access_url:
                        dist_input.access_url_status = db_dist.access_url_status
                        count_preserved += 1
                    else:
                        # URL changed, force re-check
                        dist_input.access_url_status = None

                    # Preserve Download URL Status if URL is unchanged
                    if db_dist.download_url == dist_input.download_url:
                        dist_input.download_url_status = db_dist.download_url_status
                        count_preserved += 1
                    else:
                        dist_input.download_url_status = None

        logger.info(f"Preserved cached status for {count_preserved} URLs.")

    async def run(self):
        self.init_db()
        dataset_inputs = self.load_raw_data()
        input_ids = {d.id for d in dataset_inputs}

        with self.SessionLocal() as session:
            # 1. Prune
            self.prune_records(session, input_ids)
            
            # 2. Upsert Logic (Sync DB state to Input objects)
            self.hydrate_and_sync(session, dataset_inputs)
            
            # Collect all distributions that need checking
            all_distributions = [
                d for ds in dataset_inputs 
                for d in ds.distributions
            ]
            
            # 3. Audit URLs (Async)
            logger.info("Starting URL Audit Phase...")
            await self.checker.check_distributions(all_distributions)
            
            # 4. Score & Save
            logger.info("Calculating Scores and Saving to DB...")
            
            for ds_input in dataset_inputs:
                # Compute Scores (using the now populated URL statuses)
                scores = self.scorer.compute_scores(ds_input)
                
                # Create/Merge Dataset ORM
                # We use .model_dump() to get dict, then filter keys matching ORM
                ds_data = ds_input.model_dump(include={
                    'id', 'rdf_type', 'title', 'description', 'keywords', 'themes',
                    'publisher', 'contact_point', 'business_owner', 'issued', 
                    'modified', 'access_rights', 'schema_violations_count',
                    'schema_violation_messages', 'input_quality_score'
                })
                
                # Merge calculated scores
                ds_data.update(scores)
                
                dataset_orm = Dataset(**ds_data)
                
                # Re-construct Distributions for ORM (Cascading replace)
                orm_dists = []
                for d_in in ds_input.distributions:
                    d_data = d_in.model_dump(include={
                        'identifier', 'access_url', 'download_url', 'format_type',
                        'media_type', 'license_id', 'access_url_status', 
                        'download_url_status'
                    })
                    orm_dists.append(Distribution(**d_data))
                
                dataset_orm.distributions = orm_dists
                
                # Merge into session
                session.merge(dataset_orm)
            
            session.commit()
            logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    pipeline = AuditPipeline()
    asyncio.run(pipeline.run())