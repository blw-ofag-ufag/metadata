import asyncio
import json
import logging
import sys
import aiohttp # Required for the URL checker
from typing import List, Dict, Set
from pathlib import Path
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session, sessionmaker

# Local modules
from src.config import settings
from src.models import (
    Base, Dataset, Distribution, DatasetInput, DistributionInput
)
from src.logic import QualityScorer

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for HTTP Status
HTTP_TIMEOUT = 408
HTTP_SSL_ERROR = 495
HTTP_CONNECTION_ERROR = 503
HTTP_OTHER_ERROR = 400
HTTP_OK_INTERNAL = 200 # We treat internal/file paths as implicitly "OK"

# ==============================================================================
# 1. ASYNC URL CHECKER
# ==============================================================================
class AsyncUrlChecker:
    def __init__(self):
        # Limit concurrent requests to avoid getting banned
        self.semaphore = asyncio.Semaphore(settings.ASYNC_PER_DOMAIN)
        self.headers = {"User-Agent": settings.USER_AGENT}
        self._results_cache: Dict[str, int] = {}

    def _is_web_url(self, url: str) -> bool:
        r"""
        Returns True if URL implies a network request (http/https).
        Returns False for internal paths (M:\...), ftp, or empty strings.
        """
        if not url: 
            return False
        return url.lower().startswith(("http://", "https://"))

    async def check_distributions(self, distributions: List[DistributionInput]):
        tasks = []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for dist in distributions:
                
                # --- CHECK ACCESS URL ---
                if dist.access_url:
                    if self._is_web_url(dist.access_url):
                        # It is a web URL, check if we need to audit it
                        if self.should_check(dist, "access_url"):
                            tasks.append(self._audit_url(dist, "access_url", session))
                    else:
                        # It is an internal path (e.g. M:\...) -> Mark as OK immediately
                        dist.access_url_status = HTTP_OK_INTERNAL

                # --- CHECK DOWNLOAD URL ---
                if dist.download_url:
                    if self._is_web_url(dist.download_url):
                        # It is a web URL, check if we need to audit it
                        if self.should_check(dist, "download_url"):
                            tasks.append(self._audit_url(dist, "download_url", session))
                    else:
                        # It is an internal path -> Mark as OK immediately
                        dist.download_url_status = HTTP_OK_INTERNAL
            
            if tasks:
                logger.info(f"Auditing {len(tasks)} URLs asynchronously...")
                await asyncio.gather(*tasks)

    def should_check(self, dist: DistributionInput, url_type: str) -> bool:
        # Only check if status is None (not cached/checked yet)
        current_status = getattr(dist, f"{url_type}_status")
        return current_status is None

    async def _audit_url(self, dist: DistributionInput, field_name: str, session: aiohttp.ClientSession):
        url = getattr(dist, field_name) 
        if not url: return

        # Check Cache first
        if url in self._results_cache:
            status = self._results_cache[url]
        else:
            async with self.semaphore:
                status = await self._fetch_status(url, session)
                self._results_cache[url] = status
        
        # Save result to the Pydantic model
        setattr(dist, f"{field_name}_status", status)

    async def _fetch_status(self, url: str, session: aiohttp.ClientSession) -> int:
        try:
            # We use HEAD requests to be polite and save bandwidth
            async with session.head(url, timeout=10, allow_redirects=True) as response:
                return response.status
        except asyncio.TimeoutError:
            return HTTP_TIMEOUT
        except aiohttp.ClientSSLError:
            return HTTP_SSL_ERROR
        except aiohttp.ClientConnectionError:
            return HTTP_CONNECTION_ERROR
        except Exception:
            # Fallback: sometimes servers block HEAD, try GET
            try:
                async with session.get(url, timeout=10) as response:
                    return response.status
            except Exception:
                return HTTP_OTHER_ERROR

# ==============================================================================
# 2. AUDIT PIPELINE
# ==============================================================================
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
            session.execute(delete(Dataset).where(Dataset.id.in_(to_delete)))
            session.commit()

    def hydrate_and_sync(self, session: Session, inputs: List[DatasetInput]):
        """
        Loads existing DB state to preserve previous URL check results 
        so we don't re-check valid URLs unnecessarily.
        """
        existing_dists_query = select(Distribution)
        db_dists = session.scalars(existing_dists_query).all()
        db_dist_map = {(d.dataset_id, d.identifier): d for d in db_dists if d.identifier}

        for ds_input in inputs:
            for dist_input in ds_input.distributions:
                key = (ds_input.id, dist_input.identifier)
                if key in db_dist_map:
                    db_dist = db_dist_map[key]
                    # Preserve status only if URL hasn't changed
                    if db_dist.access_url == dist_input.access_url:
                        dist_input.access_url_status = db_dist.access_url_status
                    if db_dist.download_url == dist_input.download_url:
                        dist_input.download_url_status = db_dist.download_url_status

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
            
            logger.info("Calculating Scores & Suggestions...")
            
            # --- SPLIT EXPORT STRATEGY ---
            # 1. Summary List: Lightweight, for immediate table rendering.
            # 2. Details Map: Heavyweight, lazy-loaded by ID when needed.
            summary_list = []
            details_map = {}

            for ds_input in dataset_inputs:
                # 1. Calculate Score
                analysis = self.scorer.analyze_quality(ds_input)
                
                # 2. Prepare Data for DB (Validation/History)
                ds_data = ds_input.model_dump(include={
                    'id', 'rdf_type', 'title', 'description', 'keywords', 'themes',
                    'publisher', 'contact_point', 'business_owner', 'issued', 
                    'modified', 'access_rights', 'schema_violations_count',
                    'schema_violation_messages', 'input_quality_score'
                })
                ds_data.update(analysis) # Add scores
                
                # 3. Update DB 
                dataset_orm = Dataset(**ds_data)
                orm_dists = []
                
                # Prepare Distributions List for Export
                dist_export_list = []

                for d_in in ds_input.distributions:
                    d_data = d_in.model_dump(include={
                        'identifier', 'access_url', 'download_url', 'format_type',
                        'media_type', 'license_id', 'rights', 'byte_size',
                        'access_url_status', 'download_url_status'
                    })
                    orm_dists.append(Distribution(**d_data))
                    dist_export_list.append(d_data)

                dataset_orm.distributions = orm_dists
                session.merge(dataset_orm)

                # 4. EXPORT PREPARATION
                
                # A. DETAILS RECORD (Full Data)
                detail_record = ds_data.copy()
                detail_record['distributions'] = dist_export_list
                # Store in map keyed by ID for O(1) lookup
                details_map[ds_data['id']] = detail_record

                # B. SUMMARY RECORD (Lightweight)
                # Only fields needed for the Overview Table & Charts
                summary_record = {
                    'id': ds_data['id'],
                    'title': ds_data['title'], # Keep full dict for translation
                    'swiss_score': ds_data['swiss_score'],
                    'schema_violations_count': ds_data['schema_violations_count'],
                    'schema_violation_messages': ds_data['schema_violation_messages'],
                    'modified': ds_data['modified']
                }
                summary_list.append(summary_record)
            
            session.commit()
            
            # --- EXPORT TO JSON FILES ---
            output_dir = Path("dashboard")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Write Summary (Fast Load)
            summary_path = output_dir / "data_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_list, f, ensure_ascii=False, indent=None, separators=(',', ':'))

            # 2. Write Details (Lazy Load)
            details_path = output_dir / "data_details.json"
            with open(details_path, "w", encoding="utf-8") as f:
                json.dump(details_map, f, ensure_ascii=False, indent=None, separators=(',', ':'))
            
            logger.info(f"✅ Exported: Summary ({len(summary_list)} items) & Details Map.")

if __name__ == "__main__":
    pipeline = AuditPipeline()
    asyncio.run(pipeline.run())