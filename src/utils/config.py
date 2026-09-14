"""Configuration module for Hospital Readmission Analytics project."""

from pathlib import Path
import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Central configuration parameters."""

    # Project directories
    ROOT_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    STAGING_DATA_DIR: Path = DATA_DIR / "staging"
    CLEANED_DATA_DIR: Path = DATA_DIR / "cleaned"
    REJECTED_DATA_DIR: Path = DATA_DIR / "rejected"
    SAMPLE_DATA_DIR: Path = DATA_DIR / "sample"
    LOGS_DIR: Path = BASE_DIR / "logs"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Dataset file paths
    DATASET_PATH: Path = Path(os.getenv("DATASET_PATH", "data/raw/diabetic_data.csv"))
    if not DATASET_PATH.is_absolute():
        DATASET_PATH = BASE_DIR / DATASET_PATH

    MAPPING_PATH: Path = Path(os.getenv("MAPPING_PATH", "data/raw/IDs_mapping.csv"))
    if not MAPPING_PATH.is_absolute():
        MAPPING_PATH = BASE_DIR / MAPPING_PATH

    UCI_DOWNLOAD_URL: str = os.getenv(
        "UCI_DOWNLOAD_URL",
        "https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip",
    )

    # Patient privacy salt
    PATIENT_SALT: str = os.getenv("PROJECT_PATIENT_SALT", "h0sp1t4l_r3adm1ss10n_s4lt_2024_v1")

    # PostgreSQL Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "hospital_analytics")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")

    # Schemas
    SCHEMA_STAGING: str = os.getenv("POSTGRES_SCHEMA_STAGING", "staging")
    SCHEMA_CURATED: str = os.getenv("POSTGRES_SCHEMA_CURATED", "curated")
    SCHEMA_ANALYTICS: str = os.getenv("POSTGRES_SCHEMA_ANALYTICS", "analytics")
    SCHEMA_REJECTED: str = os.getenv("POSTGRES_SCHEMA_REJECTED", "rejected")
    SCHEMA_METADATA: str = os.getenv("POSTGRES_SCHEMA_METADATA", "metadata")

    # App environment & logging
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_directories(cls):
        """Ensure all required runtime directories exist."""
        for directory in [
            cls.RAW_DATA_DIR,
            cls.STAGING_DATA_DIR,
            cls.CLEANED_DATA_DIR,
            cls.REJECTED_DATA_DIR,
            cls.SAMPLE_DATA_DIR,
            cls.LOGS_DIR,
            cls.REPORTS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_db_url(cls, async_driver: bool = False) -> str:
        """Construct standard SQLAlchemy connection URI."""
        driver = "postgresql+psycopg2"
        return f"{driver}://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"


# Initialize required directories on import
Config.ensure_directories()
