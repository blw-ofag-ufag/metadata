"""
Unified metadata processing pipeline.

This script walks through four raw-metadata directories:

    data/raw/datasets       → rdf:type dcat:Dataset
    data/raw/dataServices   → rdf:type dcat:DataServices
    data/raw/datasetSeries  → rdf:type dcat:DatasetSeries
    data/raw/catalogs       → rdf:type dcat:Catalog

Every *.json file found is:

1. Loaded from the corresponding raw directory.
2. Validated against the corresponding Draft-7 JSON Schema.
3. Enriched with:
       - dataOwner
       - schemaViolations
       - schemaViolationMessages
       - quality

The quality score is calculated as:

    quality = file_size / (schema_violations + 1)

Instead of combining all records into one output file, records are now
grouped by metadata class and written to separate files:

    data/processed/datasets.json
    data/processed/datasetSeries.json
    data/processed/dataServices.json
    data/processed/catalogs.json

Each output file is sorted by quality, with the highest quality first.
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

# Base data directory.
#
# This assumes the script is run from the project root and that the
# following directory structure exists:
#
# data/
# ├── raw/
# │   ├── datasets/
# │   ├── dataServices/
# │   ├── datasetSeries/
# │   └── catalogs/
# ├── schemas/
# │   ├── dataset.json
# │   ├── dataService.json
# │   ├── datasetSeries.json
# │   └── catalog.json
# └── processed/
#
BASE_DIR = Path(os.path.expanduser("data"))

RAW_DIR = BASE_DIR / "raw"
SCHEMA_DIR = BASE_DIR / "schemas"
PROCESSED_DIR = BASE_DIR / "processed"


# ---------------------------------------------------------------------------
# Metadata class configuration
# ---------------------------------------------------------------------------
#
# Each metadata class defines:
#
#   dir    → where the raw JSON files are located
#   schema → which JSON Schema should be used for validation
#   output → where the processed records should be written
#
# The main benefit of defining the output here is that the processing
# logic below does not need separate hard-coded writing logic for every
# metadata type.
#

CLASSES = {
    "dcat:Dataset": {
        "dir": RAW_DIR / "datasets",
        "schema": SCHEMA_DIR / "dataset.json",
        "output": PROCESSED_DIR / "datasets.json",
    },
    "dcat:DataServices": {
        "dir": RAW_DIR / "dataServices",
        "schema": SCHEMA_DIR / "dataService.json",
        "output": PROCESSED_DIR / "dataServices.json",
    },
    "dcat:DatasetSeries": {
        "dir": RAW_DIR / "datasetSeries",
        "schema": SCHEMA_DIR / "datasetSeries.json",
        "output": PROCESSED_DIR / "datasetSeries.json",
    },
    "dcat:Catalog": {
        "dir": RAW_DIR / "catalogs",
        "schema": SCHEMA_DIR / "catalog.json",
        "output": PROCESSED_DIR / "catalogs.json",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def load_schema(schema_path: Path) -> Optional[dict]:
    """
    Load and memoise a JSON Schema file.

    The @lru_cache decorator means that if the same schema is needed
    multiple times, it is only loaded from disk once.
    """

    try:
        with schema_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    except Exception as exc:  # pragma: no cover
        print(f"Error loading schema {schema_path}: {exc}")
        return None


def _schema_errors(data: dict, schema: dict) -> List[str]:
    """
    Validate a JSON object against a JSON Schema.

    Returns a list containing the error messages for all validation
    violations.
    """

    validator = Draft7Validator(schema)

    return [
        error.message
        for error in validator.iter_errors(data)
    ]


def _extract_business_owner(
    mapping: Dict[str, Any],
) -> Optional[Any]:
    """
    Extract the business/data owner from prov:qualifiedAttribution.

    The owner is identified by:

        dcat:hadRole == "dataOwner"

    If no such attribution exists, None is returned.
    """

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
    """
    Validate and enrich a single metadata record.

    The following fields are added to the original metadata:

        rdf:type
        dataOwner
        schemaViolations
        schemaViolationMessages
        quality

    The original prov:qualifiedAttribution field is removed after the
    business owner has been extracted.
    """

    # -----------------------------------------------------------------------
    # 1. Schema validation
    # -----------------------------------------------------------------------
    #
    # Validate the original metadata before modifying it.
    #
    violation_messages = _schema_errors(data, schema)
    violations = len(violation_messages)

    # -----------------------------------------------------------------------
    # 2. Extract business owner
    # -----------------------------------------------------------------------
    #
    # Extract the owner before removing prov:qualifiedAttribution.
    #
    owner = _extract_business_owner(data)

    # Remove prov:qualifiedAttribution from the final output.
    #
    # This is done regardless of whether an owner was found.
    #
    data.pop("prov:qualifiedAttribution", None)

    # -----------------------------------------------------------------------
    # 3. Calculate quality
    # -----------------------------------------------------------------------
    #
    # File size is measured in bytes.
    #
    # A record with no schema violations gets:
    #
    #     quality = file_size / 1
    #
    # More violations reduce the quality score.
    #
    file_size = file_path.stat().st_size
    quality = file_size / (violations + 1)

    # -----------------------------------------------------------------------
    # 4. Assemble enriched record
    # -----------------------------------------------------------------------
    #
    # OrderedDict is used to preserve the desired field order:
    #
    #   1. rdf:type
    #   2. original metadata
    #   3. calculated/enriched fields
    #
    enriched: "OrderedDict[str, Any]" = OrderedDict()

    # rdf:type should appear first.
    enriched["rdf:type"] = cls

    # Add all original metadata, except prov:qualifiedAttribution,
    # which was removed above.
    enriched.update(data)

    # Add calculated fields at the end.
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
    """
    Process all supported metadata classes.

    Unlike the original implementation, records are kept separately
    for each metadata class.

    For example:

        dcat:Dataset
            → data/processed/datasets.json

        dcat:DataServices
            → data/processed/dataServices.json

        dcat:DatasetSeries
            → data/processed/datasetSeries.json

        dcat:Catalog
            → data/processed/catalogs.json
    """

    # -----------------------------------------------------------------------
    # Create one empty list for each supported metadata class.
    # -----------------------------------------------------------------------
    #
    # Original implementation:
    #
    #     combined = []
    #
    # This meant all datasets, services and series ended up in the same
    # output file.
    #
    # Now we have:
    #
    #     combined["dcat:Dataset"]
    #     combined["dcat:DataServices"]
    #     combined["dcat:DatasetSeries"]
    #     combined["dcat:Catalog"]
    #
    combined: Dict[str, List[Dict[str, Any]]] = {
        cls: []
        for cls in CLASSES
    }

    # -----------------------------------------------------------------------
    # Process each metadata class
    # -----------------------------------------------------------------------

    for cls, cfg in CLASSES.items():

        # Load the JSON Schema for this metadata class.
        schema = load_schema(cfg["schema"])

        if schema is None:
            print(f"Skipping {cls}: schema not available")
            continue

        # Get the raw directory for this class.
        directory = cfg["dir"]

        # If the raw directory does not exist, skip processing it.
        #
        # The output file will still be created later as an empty JSON
        # array. This ensures that every configured output file exists.
        #
        if not directory.exists():
            print(
                f"Directory for class '{cls}' "
                f"does not exist: {directory}"
            )
            continue

        # -------------------------------------------------------------------
        # Process every JSON file in the raw directory.
        # -------------------------------------------------------------------

        for file_path in sorted(directory.glob("*.json")):

            try:
                # Load the raw JSON metadata.
                with file_path.open("r", encoding="utf-8") as fp:
                    data = json.load(fp)

                # Validate and enrich the record.
                record = enrich_record(
                    data=data,
                    file_path=file_path,
                    cls=cls,
                    schema=schema,
                )

                # IMPORTANT:
                #
                # Add the record only to the list belonging to its class.
                #
                # This is the main behavioral change compared with the
                # original script.
                #
                combined[cls].append(record)

            except Exception as exc:  # pragma: no cover
                print(
                    f"Error processing {file_path}: {exc}"
                )

    # -----------------------------------------------------------------------
    # Make sure the processed directory exists.
    # -----------------------------------------------------------------------
    #
    # mkdir(..., exist_ok=True) means:
    #
    # - create the directory if it doesn't exist
    # - do nothing if it already exists
    #
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------------------------
    # Sort and write each metadata class separately.
    # -----------------------------------------------------------------------
    #
    # Every class gets its own output file.
    #
    for cls, records in combined.items():

        # Sort records by quality, highest quality first.
        records.sort(
            key=lambda record: record.get("quality", 0.0),
            reverse=True,
        )

        # Get the output path configured for this class.
        output_file = CLASSES[cls]["output"]

        # Write the records as a JSON array.
        #
        # If no records were found, this writes:
        #
        #     []
        #
        # Therefore the corresponding output file is still created.
        #
        with output_file.open("w", encoding="utf-8") as fp:
            json.dump(
                records,
                fp,
                ensure_ascii=False,
                indent=4,
            )

        print(
            f"Wrote {len(records)} records to {output_file}"
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_all_files()