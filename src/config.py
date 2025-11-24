from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # --- Project Paths ---
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_FILE: Path = DATA_DIR / "processed" / "datasets.json"
    DB_URL: str | None = None

    # --- Scoring Weights ---
    # These defaults mirror the opendata.swiss logic but allow override via .env
    
    # Findability
    WEIGHT_FINDABILITY_KEYWORDS: int = 30
    WEIGHT_FINDABILITY_CATEGORIES: int = 30
    WEIGHT_FINDABILITY_GEO_SEARCH: int = 20
    WEIGHT_FINDABILITY_TIME_SEARCH: int = 20

    # Accessibility
    WEIGHT_ACCESSIBILITY_ACCESS_URL: int = 50
    WEIGHT_ACCESSIBILITY_DOWNLOAD_URL: int = 20
    WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID: int = 30

    # Interoperability
    WEIGHT_INTEROP_FORMAT: int = 20
    WEIGHT_INTEROP_MEDIA_TYPE: int = 10
    WEIGHT_INTEROP_VOCABULARY: int = 10
    WEIGHT_INTEROP_NON_PROPRIETARY: int = 20
    WEIGHT_INTEROP_MACHINE_READABLE: int = 20
    WEIGHT_INTEROP_DCAT_AP: int = 30

    # Reusability
    WEIGHT_REUSE_LICENSE: int = 20
    WEIGHT_REUSE_LICENSE_VOCAB: int = 10
    WEIGHT_REUSE_ACCESS_RESTRICTION: int = 10
    WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB: int = 5
    WEIGHT_REUSE_CONTACT_POINT: int = 20
    WEIGHT_REUSE_PUBLISHER: int = 10

    # Contextuality
    WEIGHT_CONTEXT_RIGHTS: int = 5
    WEIGHT_CONTEXT_FILE_SIZE: int = 5
    WEIGHT_CONTEXT_ISSUE_DATE: int = 5
    WEIGHT_CONTEXT_MODIFICATION_DATE: int = 5

    # --- Application Settings ---
    DEBUG_MODE: bool = False
    # Control concurrency for URL checking to avoid DOS protection triggers
    ASYNC_PER_DOMAIN: int = 1 

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def model_post_init(self, __context):
        """
        Automatically set the DB_URL to an absolute path inside the data/ folder
        if it wasn't provided in the .env file.
        """
        if self.DB_URL is None:
            # On Linux (Posit), absolute paths need 4 slashes: sqlite:////home/...
            self.DB_URL = f"sqlite:///{self.DATA_DIR.absolute()}/qa.db"

settings = Settings()