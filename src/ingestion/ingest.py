"""Raw Ingestion Layer module.

Verifies raw input, calculates cryptographic checksums, logs ingestion metadata,
and loads raw data into staging representation without destructive transformations.
"""

import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pandas as pd

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file in streaming chunks."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


class IngestionManager:
    """Manages raw dataset verification, audit metadata, and staging ingestion."""

    def __init__(self, raw_path: Optional[Path] = None, run_id: Optional[str] = None):
        self.raw_path = Path(raw_path) if raw_path else Config.DATASET_PATH
        self.run_id = run_id or datetime.now(timezone.utc).strftime("RUN_%Y%m%d_%H%M%S")
        self.metadata: dict = {}

    def verify_and_audit_raw(self) -> dict:
        """Verifies raw dataset file and records ingestion metadata."""
        logger.info(f"[{self.run_id}] Verifying raw file at: {self.raw_path}")

        if not self.raw_path.exists():
            err_msg = f"Raw dataset file not found at: {self.raw_path}"
            logger.error(err_msg)
            self.metadata = {
                "source_name": "UCI Machine Learning Repository",
                "source_file": str(self.raw_path.name),
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "file_checksum": "",
                "file_size_bytes": 0,
                "row_count": 0,
                "column_count": 0,
                "status": "FAILED",
                "error_message": err_msg,
                "pipeline_run_id": self.run_id,
            }
            raise FileNotFoundError(err_msg)

        file_size = self.raw_path.stat().st_size
        checksum = compute_sha256(self.raw_path)

        # Read header and count rows
        df_preview = pd.read_csv(self.raw_path, nrows=5)
        column_count = len(df_preview.columns)

        # Accurate row count without loading full file into memory at once
        with open(self.raw_path, "r", encoding="utf-8", errors="ignore") as f:
            row_count = sum(1 for _ in f) - 1  # subtract header

        self.metadata = {
            "source_name": "UCI Diabetes 130-US Hospitals (1999-2008)",
            "source_file": str(self.raw_path.name),
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "file_checksum": checksum,
            "file_size_bytes": file_size,
            "row_count": row_count,
            "column_count": column_count,
            "status": "SUCCESS",
            "error_message": None,
            "pipeline_run_id": self.run_id,
        }

        logger.info(
            f"[{self.run_id}] Raw file verified: {row_count} rows, {column_count} columns, "
            f"size: {file_size} bytes, SHA-256: {checksum[:12]}..."
        )
        return self.metadata

    def stage_dataset(self) -> pd.DataFrame:
        """Loads raw dataset into staging representation preserving all original columns."""
        if not self.metadata or self.metadata.get("status") != "SUCCESS":
            self.verify_and_audit_raw()

        logger.info(f"[{self.run_id}] Staging raw data from {self.raw_path}...")
        df_staging = pd.read_csv(self.raw_path, dtype=str)

        # Add audit columns to staging
        df_staging["pipeline_run_id"] = self.run_id
        df_staging["staged_at"] = datetime.now(timezone.utc).isoformat()

        # Persist local staging copy
        staging_file = Config.STAGING_DATA_DIR / f"staging_diabetic_encounters_{self.run_id}.parquet"
        df_staging.to_parquet(staging_file, index=False)

        # Also maintain standard symlink or latest file for quick access
        latest_staging = Config.STAGING_DATA_DIR / "staging_diabetic_encounters_latest.parquet"
        df_staging.to_parquet(latest_staging, index=False)

        logger.info(
            f"[{self.run_id}] Successfully staged {len(df_staging)} rows to {staging_file}"
        )
        return df_staging


if __name__ == "__main__":
    manager = IngestionManager()
    manager.verify_and_audit_raw()
    manager.stage_dataset()
