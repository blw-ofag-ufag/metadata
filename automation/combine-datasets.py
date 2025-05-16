"""Dataset processing pipeline

This script scans every JSON metadata file inside ``data/raw/datasets``,
validates it against the Draft‑7 JSON‑Schema defined in
``data/schemas/dataset.json``, extracts a curated subset of attributes and
computes a *quality* score for each dataset. The resulting list of objects is
sorted in descending order of quality and written to
``data/processed/datasets.json``.

Quality is defined as:

    quality = file_size / (schema_violations + 1)

where *file_size* is the size of the original JSON file (in bytes) and
*schema_violations* is the number of JSON‑Schema errors detected. Using
`(schema_violations + 1)` avoids a division‑by‑zero error for perfect files; in that case
the score falls back to the file size itself.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft7Validator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_DIR = Path(os.path.expanduser("data/raw/datasets"))
OUTPUT_FILE = Path(os.path.expanduser("data/processed/datasets.json"))
SCHEMA_FILE = Path(os.path.expanduser("data/schemas/dataset.json"))

# Attributes to extract (``prov:qualifiedAttribution`` is only used to derive
# the ``businessDataOwner`` field and is removed afterwards).
ATTRIBUTES = [
    "dct:identifier",
    "dct:title",
    "dct:description",
    "dct:issued",
    "dcat:keyword",
    "prov:qualifiedAttribution",
    "schema:image",
    "dct:accessRights",
    "dct:publisher",
    "dcat:contactPoint",
    "dct:modified",
    "adms:status",
    "bv:classification",
    "bv:personalData",
    "bv:archivalValue",
    "dcatap:availability",
    "bv:typeOfData",
    "dcat:theme",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_schema(schema_path: Path) -> Optional[dict]:
    """Load a JSON‑Schema file and return it as a Python *dict*."""
    try:
        with schema_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception as exc:  # pragma: no cover – log & propagate gracefully
        print(f"Error loading schema from {schema_path}: {exc}")
        return None

def _schema_errors(data: dict, schema: dict) -> List[str]:
    """Return a list with the *messages* of all schema violations."""
    validator = Draft7Validator(schema)
    return [error.message for error in validator.iter_errors(data)]

def extract_relevant_data(file_path: Path, schema: dict) -> Optional[Dict[str, Any]]:
    """Read *file_path* and return a filtered & enriched mapping.

    The function extracts the subset of attributes defined in *ATTRIBUTES*,
    derives ``businessDataOwner`` from ``prov:qualifiedAttribution``, counts
    JSON‑Schema violations, computes a quality score and returns the resulting
    mapping. Any exceptions are caught and logged; *None* is returned on
    failure so the caller can skip the file.
    """

    try:
        # 1. Load JSON --------------------------------------------------------
        with file_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)

        # 2. Schema validation -----------------------------------------------
        violation_messages = _schema_errors(data, schema)
        violations_count = len(violation_messages)

        # 3. Attribute filtering ---------------------------------------------
        extracted: Dict[str, Any] = {k: data[k] for k in ATTRIBUTES if k in data}

        # 4. businessDataOwner derivation ------------------------------------
        if "prov:qualifiedAttribution" in extracted:
            for role in extracted["prov:qualifiedAttribution"]:
                if role.get("dcat:hadRole") == "businessDataOwner":
                    extracted["businessDataOwner"] = role.get("prov:agent")
                    break
            extracted.pop("prov:qualifiedAttribution", None)

        # 5. Quality score ----------------------------------------------------
        file_size = file_path.stat().st_size  # bytes
        quality = file_size / (violations_count + 1)

        # 6. Augment result ---------------------------------------------------
        extracted.update(
            {
                "schemaViolations": violations_count,
                "schemaViolationMessages": violation_messages,
                "quality": quality,
            }
        )
        return extracted

    except Exception as exc:  # pragma: no cover – log & propagate gracefully
        print(f"Error processing {file_path}: {exc}")
        return None

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_all_files() -> None:
    """Run the full pipeline and write the combined output JSON."""

    schema = load_schema(SCHEMA_FILE)
    if schema is None:
        print("Schema could not be loaded. Exiting.")
        return

    combined_data: List[Dict[str, Any]] = []

    # Iterate over *all* *.json files – ignore nested subdirectories for now.
    for file_path in sorted(DATASET_DIR.glob("*.json")):
        result = extract_relevant_data(file_path, schema)
        if result is not None:
            combined_data.append(result)

    # Sort by quality (descending: highest quality first) --------------------
    combined_data.sort(key=lambda item: item.get("quality", 0.0), reverse=True)

    # Ensure output directory exists ----------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Persist ----------------------------------------------------------------
    with OUTPUT_FILE.open("w", encoding="utf-8") as fp:
        json.dump(combined_data, fp, ensure_ascii=False, indent=4)

    print(f"Combined {len(combined_data)} datasets into {OUTPUT_FILE}")

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    process_all_files()
