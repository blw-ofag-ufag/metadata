"""
This script collects all `dcat:keyword` values from the aggregated
metadata file created by `metadata_pipeline.py` and
writes them to a dedicated JSON file for downstream use.

All keywords are treated as case-sensitive strings when de-duplicating, 
but the final list is sorted alphanumerically (case‑insensitive).

Individual records may provide keywords as a single string or as an array
of strings – both forms are accepted.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

BASE_DIR = Path(os.path.expanduser("data"))
INPUT_FILE = BASE_DIR / "processed" / "datasets.json"
OUTPUT_FILE = BASE_DIR / "processed" / "keywords.json"

def _flatten_keywords(values: Any) -> Iterable[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        # filter out non-string items defensively
        return [str(v) for v in values if isinstance(v, (str, bytes))]
    # Fallback – treat anything else as a single string representation
    return [str(values)]

def _alphanum_key(s: str) -> List[Any]:
    return [int(text) if text.isdigit() else text.casefold() for text in re.split(r"(\d+)", s)]

def extract_keywords() -> None:
    """Read all records, collect unique keywords, sort, and write output file."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    with INPUT_FILE.open("r", encoding="utf-8") as fp:
        records: List[Dict[str, Any]] = json.load(fp)

    seen: "dict[str, None]" = {}

    for record in records:
        for kw in _flatten_keywords(record.get("dcat:keyword")):
            seen.setdefault(kw, None)

    # Natural alphanumeric sort
    keywords: List[str] = sorted(seen.keys(), key=_alphanum_key)

    # Ensure destination directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as fp:
        json.dump({"dcat:keyword": keywords}, fp, ensure_ascii=False, indent=4)

    print(f"Extracted {len(keywords)} unique keywords → {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_keywords()
