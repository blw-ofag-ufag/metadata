import pytest
import json
import os
from src.config import settings
from src.audit import AuditPipeline
from src.models import Dataset
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# --- FIXTURES ---

@pytest.fixture(scope="function")
def setup_test_env(tmp_path):
    """Sets up a temporary DB and Data file for each test."""
    # 1. Override Paths
    d_file = tmp_path / "datasets.json"
    db_file = tmp_path / "test.db"
    
    settings.RAW_DATA_FILE = d_file
    settings.DB_URL = f"sqlite:///{db_file}"
    
    return d_file, db_file

# --- TESTS ---

@pytest.mark.asyncio
async def test_pipeline_ingest_and_score(setup_test_env):
    data_file, _ = setup_test_env
    
    # Create Dummy Data
    raw_data = [{
        "dct:identifier": "test-1",
        "dct:title": {"de": "Test"},
        "dct:description": {"de": "Desc"},
        "dct:publisher": "BLW",
        "dct:issued": "2023-01-01",
        "adms:status": "published",
        "bv:classification": "none",
        "bv:personalData": "none",
        "dcat:keyword": ["test"],
        "dcat:distribution": [{
            "dcat:accessURL": "https://example.com",
            "dct:format": "CSV",
            "dcat:mediaType": "text/csv"
        }]
    }]
    
    with open(data_file, "w") as f:
        json.dump(raw_data, f)
        
    # Run Pipeline
    pipeline = AuditPipeline()
    await pipeline.run()
    
    # Verify
    engine = create_engine(settings.DB_URL)
    with Session(engine) as session:
        dataset = session.get(Dataset, "test-1")
        assert dataset is not None
        assert dataset.swiss_score > 0  # Should have scored points for format/keywords
        assert len(dataset.distributions) == 1
        # Example.com usually returns 200
        assert dataset.distributions[0].access_url_status == 200

@pytest.mark.asyncio
async def test_pruning(setup_test_env):
    data_file, _ = setup_test_env
    pipeline = AuditPipeline()
    
    # 1. Ingest two records
    with open(data_file, "w") as f:
        json.dump([
            {"dct:identifier": "id-1", "dct:title": {"de": "1"}, "adms:status": "published", "bv:classification": "none", "bv:personalData": "none"},
            {"dct:identifier": "id-2", "dct:title": {"de": "2"}, "adms:status": "published", "bv:classification": "none", "bv:personalData": "none"}
        ], f)
    await pipeline.run()
    
    # 2. Ingest only one (simulate deletion of id-2)
    with open(data_file, "w") as f:
        json.dump([
            {"dct:identifier": "id-1", "dct:title": {"de": "1"}, "adms:status": "published", "bv:classification": "none", "bv:personalData": "none"}
        ], f)
    await pipeline.run()
    
    # Verify
    engine = create_engine(settings.DB_URL)
    with Session(engine) as session:
        ids = session.scalars(select(Dataset.id)).all()
        assert "id-1" in ids
        assert "id-2" not in ids