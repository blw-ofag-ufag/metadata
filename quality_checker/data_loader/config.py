import os
from pathlib import Path

# Versioning.
VERSION = 1.0
VERSION_DATE = "03.09.2025"

# Environment Variables keys.
ENV_AUDIT_DEV = "AUDIT_DEV"
ENV_SHARED = "SHARED"
ENV_AUDIT_HTTP_PROXY = "AUDIT_HTTP_PROXY"
ENV_AUDIT_HTTPS_PROXY = "AUDIT_HTTPS_PROXY"

# Base Paths.
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
PACKAGE_DIR = ROOT_DIR / "package"

# Controlled Vocabularies.
CONTROLLED_VOC_DIR = DATA_DIR / "controlled_vocabulary"
MEDIATYPE = CONTROLLED_VOC_DIR / "Media Types.xml"
ACCESS_RIGHTS = CONTROLLED_VOC_DIR / 'access-rights_preprocessed.json'

# Input Files.
INPUT_FILE = DATA_DIR / "input_raw" / "all_catalog.jsonld"

# Output Files.
OUT = (
    DATA_DIR / "output" 
    if os.getenv(ENV_AUDIT_DEV) == "1"
    else Path(os.getenv(ENV_SHARED, "/shared/"))
)
OUTPUT_DATASET_AUDIT = OUT / "audit_dataset.json"
OUTPUT_ORG_AUDIT = OUT / "audit_organisation.json"
OUTPUT_TOTAL_AUDIT = OUT / "audit_total.json"
OUTPUT_LIST = OUT / "detailed_organisation_list.json"
OUTPUT_STATUS = OUT / "status.json"

