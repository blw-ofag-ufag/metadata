import asyncio
import json
import logging
import sys
from typing import List, Dict, Set

import aiohttp
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.models import Base, Dataset, Distribution, DatasetInput, DistributionInput
from src.logic import QualityScorer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        current = getattr(dist, f"{url_type}_status")
        return current is None

    async def _audit_url(self, dist: DistributionInput, field_name: str, session: aiohttp.ClientSession):
        url = getattr(dist, field_name) 
        if not url: return

        if url in self._results_cache:
            status = self._results_cache[url]
        else:
            async with self.semaphore:
                try:
                    async with session.head(url, timeout=10, allow_redirects=True) as r:
                        status = r.status
                except: status = 400
                self._results_cache[url] = status
        
        setattr(dist, f"{field_name}_status", status)

class AuditPipeline:
    def __init__(self):
        self.engine = create_engine(settings.DB_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.checker = AsyncUrlChecker()
        self.scorer = QualityScorer()

    def run_sync(self):
        asyncio.run(self.run())

    async def run(self):
        Base.metadata.create_all(self.engine)
        
        if not settings.RAW_DATA_FILE.exists():
            logger.error("Raw data not found")
            return

        with open(settings.RAW_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        inputs = [DatasetInput(**d) for d in raw]
        input_ids = {d.id for d in inputs}

        with self.SessionLocal() as session:
            # Prune
            existing = set(session.scalars(select(Dataset.id)).all())
            to_del = existing - input_ids
            if to_del:
                session.execute(delete(Dataset).where(Dataset.id.in_(to_del)))
                session.commit()
            
            # Sync URL status from DB to Input to avoid re-checking
            db_dists = session.scalars(select(Distribution)).all()
            map_dists = {(d.dataset_id, d.identifier): d for d in db_dists if d.identifier}
            
            for ds in inputs:
                for d in ds.distributions:
                    key = (ds.id, d.identifier)
                    if key in map_dists:
                        existing_d = map_dists[key]
                        if existing_d.access_url == d.access_url:
                            d.access_url_status = existing_d.access_url_status
                        if existing_d.download_url == d.download_url:
                            d.download_url_status = existing_d.download_url_status

            # Audit
            all_dists = [d for ds in inputs for d in ds.distributions]
            await self.checker.check_distributions(all_dists)

            # Save
            logger.info("Saving to DB...")
            for ds_in in inputs:
                scores = self.scorer.compute_scores(ds_in)
                
                # --- CRITICAL: SAVE ALL FIELDS ---
                ds_data = ds_in.model_dump(include={
                    'id', 'rdf_type', 'title', 'description', 'keywords', 'themes',
                    'publisher', 'contact_point', 'business_owner', 'issued', 
                    'modified', 'access_rights', 'schema_violations_count',
                    'schema_violation_messages', 'input_quality_score',
                    'spatial', 'temporal' # <--- ADDED
                })
                ds_data.update(scores)
                
                orm = Dataset(**ds_data)
                orm_dists = []
                for d_in in ds_in.distributions:
                    d_data = d_in.model_dump(include={
                        'identifier', 'access_url', 'download_url', 'format_type',
                        'media_type', 'license_id', 'access_url_status', 
                        'download_url_status', 'rights', 'byte_size' # <--- ADDED
                    })
                    orm_dists.append(Distribution(**d_data))
                
                orm.distributions = orm_dists
                session.merge(orm)
            
            session.commit()
            logger.info("Done.")

if __name__ == "__main__":
    AuditPipeline().run_sync()