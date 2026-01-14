"""Unified metadata processing pipeline

This script walks through three raw‑metadata directories

* ``data/raw/datasets``       → rdf:type dcat:Dataset
* ``data/raw/dataServices``   → rdf:type dcat:DataServices
* ``data/raw/datasetSeries``  → rdf:type dcat:DatasetSeries

Every `*.json` file found is validated against the corresponding
Draft‑7 JSON‑Schema and enriched with a *quality* score:

    quality = file_size / (schema_violations + 1)

The result is a single, quality‑sorted list written to
`data/processed/datasets.json`.
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft7Validator

# ---------------------------------------------------------------------------
# Configuration                                                               
# ---------------------------------------------------------------------------

BASE_DIR = Path(os.path.expanduser("data"))
RAW_DIR = BASE_DIR / "raw"
SCHEMA_DIR = BASE_DIR / "schemas"
OUTPUT_FILE = BASE_DIR / "processed" / "datasets.json"

CLASSES = {
    "dcat:Dataset": {
        "dir": RAW_DIR / "datasets",
        "schema": SCHEMA_DIR / "dataset.json",
    },
    "dcat:DataServices": {
        "dir": RAW_DIR / "dataServices",
        "schema": SCHEMA_DIR / "dataService.json",
    },
    "dcat:DatasetSeries": {
        "dir": RAW_DIR / "datasetSeries",
        "schema": SCHEMA_DIR / "datasetSeries.json",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def load_schema(schema_path: Path) -> Optional[dict]:
    """Load and memoise a JSON‑Schema file."""
    try:
        with schema_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception as exc:  # pragma: no cover
        print(f"Error loading schema {schema_path}: {exc}")
        return None

def _schema_errors(data: dict, schema: dict) -> List[str]:
    validator = Draft7Validator(schema)
    return [err.message for err in validator.iter_errors(data)]

def _extract_business_owner(mapping: Dict[str, Any]) -> Optional[Any]:
    for role in mapping.get("prov:qualifiedAttribution", []):
        if role.get("dcat:hadRole") == "dataOwner":
            return role.get("prov:agent")
    return None

def enrich_record(
    *,
    data: Dict[str, Any],
    file_path: Path,
    cls: str,
    schema: dict,
) -> Dict[str, Any]:
    
    # Compute enrichment (quality, violations, owner, class).

    #–– 1. Schema validation –––––––––––––––––––––––––––––––––––––––––––––––––
    violation_messages = _schema_errors(data, schema)
    violations = len(violation_messages)

    #–– 2. Business owner –––––––––––––––––––––––––––––––––––––––––––––––––––
    owner = _extract_business_owner(data)

    # Remove prov:qualifiedAttribution whether owner found or not
    data.pop("prov:qualifiedAttribution", None)

    #–– 3. Quality ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    file_size = file_path.stat().st_size  # bytes
    quality = file_size / (violations + 1)

    #–– 4. Assemble –––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    enriched: "OrderedDict[str, Any]" = OrderedDict()
    enriched["rdf:type"] = cls  # appears first

    # All original metadata (minus prov:qualifiedAttribution) next
    enriched.update(data)

    # Computed fields last
    enriched.update(
        {
            "dataOwner": owner,
            "schemaViolations": violations,
            "schemaViolationMessages": violation_messages,
            "quality": quality,
        }
    )

    return enriched

# ---------------------------------------------------------------------------
# Main pipeline                                                               
# ---------------------------------------------------------------------------

def process_all_files() -> None:
    """Run pipeline over all supported classes."""

    combined: List[Dict[str, Any]] = []

    for cls, cfg in CLASSES.items():
        schema = load_schema(cfg["schema"])
        if schema is None:
            print(f"Skipping {cls}: schema not available")
            continue

        directory = cfg["dir"]
        if not directory.exists():
            print(f"Directory for class '{cls}' does not exist: {directory}")
            continue

        for file_path in sorted(directory.glob("*.json")):
            try:
                with file_path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)
                record = enrich_record(
                    data=data, file_path=file_path, cls=cls, schema=schema
                )
                combined.append(record)
            except Exception as exc:  # pragma: no cover
                print(f"Error processing {file_path}: {exc}")

    # Sort by quality – best first
    combined.sort(key=lambda r: r.get("quality", 0.0), reverse=True)

    # Ensure destination exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as fp:
        json.dump(combined, fp, ensure_ascii=False, indent=4)

    print(f"Wrote {len(combined)} records to {OUTPUT_FILE}")

# ---------------------------------------------------------------------------
# Entrypoint                                                                  
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_all_files()
