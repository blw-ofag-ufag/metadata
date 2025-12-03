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
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.ASYNC_PER_DOMAIN)
        self.headers = {"User-Agent": settings.USER_AGENT}
        self._results_cache: Dict[str, int] = {}

    async def check_distributions(self, distributions: List[DistributionInput]):
        tasks = []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for dist in distributions:
                if dist.access_url and self.should_check(dist, "access_url"):
                    tasks.append(self._audit_url(dist, "access_url", session))
                if dist.download_url and self.should_check(dist, "download_url"):
                    tasks.append(self._audit_url(dist, "download_url", session))
            
            if tasks:
                logger.info(f"Auditing {len(tasks)} URLs asynchronously...")
                await asyncio.gather(*tasks)

    def should_check(self, dist: DistributionInput, url_type: str) -> bool:
        current_status = getattr(dist, f"{url_type}_status")
        if current_status is None:
            return True
        return False

    async def _audit_url(self, dist: DistributionInput, field_name: str, session: aiohttp.ClientSession):
        url = getattr(dist, field_name) 
        if not url: return

        if url in self._results_cache:
            status = self._results_cache[url]
        else:
            async with self.semaphore:
                status = await self._fetch_status(url, session)
                self._results_cache[url] = status
        
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
        except Exception:
            return HTTP_OTHER_ERROR


class AuditPipeline:
    def __init__(self):
        self.engine = create_engine(settings.DB_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.checker = AsyncUrlChecker()
        self.scorer = QualityScorer()

    def init_db(self):
        Base.metadata.create_all(self.engine)

    def load_raw_data(self) -> List[DatasetInput]:
        if not settings.RAW_DATA_FILE.exists():
            logger.error(f"Raw data file not found: {settings.RAW_DATA_FILE}")
            sys.exit(1)
        with open(settings.RAW_DATA_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        logger.info(f"Loaded {len(raw_data)} records from JSON.")
        return [DatasetInput(**d) for d in raw_data]

    def prune_records(self, session: Session, input_ids: Set[str]):
        stmt = select(Dataset.id)
        existing_ids = set(session.scalars(stmt).all())
        to_delete = existing_ids - input_ids
        if to_delete:
            logger.info(f"Pruning {len(to_delete)} obsolete datasets.")
            session.execute(delete(Dataset).where(Dataset.id.in_(to_delete)))
            session.commit()

    def hydrate_and_sync(self, session: Session, inputs: List[DatasetInput]):
        existing_dists_query = select(Distribution)
        db_dists = session.scalars(existing_dists_query).all()
        db_dist_map = {(d.dataset_id, d.identifier): d for d in db_dists if d.identifier}

        count_preserved = 0
        for ds_input in inputs:
            for dist_input in ds_input.distributions:
                key = (ds_input.id, dist_input.identifier)
                if key in db_dist_map:
                    db_dist = db_dist_map[key]
                    if db_dist.access_url == dist_input.access_url:
                        dist_input.access_url_status = db_dist.access_url_status
                        count_preserved += 1
                    else:
                        dist_input.access_url_status = None

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
            self.prune_records(session, input_ids)
            self.hydrate_and_sync(session, dataset_inputs)
            
            all_distributions = [d for ds in dataset_inputs for d in ds.distributions]
            
            logger.info("Starting URL Audit Phase...")
            await self.checker.check_distributions(all_distributions)
            
            logger.info("Calculating Scores and Suggestions...")
            
            for ds_input in dataset_inputs:
                # UPDATED: Using analyze_quality to get both scores and suggestions
                analysis = self.scorer.analyze_quality(ds_input)
                
                ds_data = ds_input.model_dump(include={
                    'id', 'rdf_type', 'title', 'description', 'keywords', 'themes',
                    'publisher', 'contact_point', 'business_owner', 'issued', 
                    'modified', 'access_rights', 'schema_violations_count',
                    'schema_violation_messages', 'input_quality_score'
                })
                
                # Merge Analysis results (scores + quality_suggestions)
                ds_data.update(analysis)
                
                dataset_orm = Dataset(**ds_data)
                
                orm_dists = []
                for d_in in ds_input.distributions:
                    d_data = d_in.model_dump(include={
                        'identifier', 'access_url', 'download_url', 'format_type',
                        'media_type', 'license_id', 'access_url_status', 
                        'download_url_status'
                    })
                    orm_dists.append(Distribution(**d_data))
                
                dataset_orm.distributions = orm_dists
                session.merge(dataset_orm)
            
            session.commit()
            logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    pipeline = AuditPipeline()
    asyncio.run(pipeline.run())