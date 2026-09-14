"""Data Quality and Validation Framework.

Implements deterministic quality checks:
- Schema completeness and unexpected column detection
- Primary key nullity and uniqueness checks
- Numeric non-negativity bounds
- Categorical domain integrity
- Rejection routing to isolated rejected-records dataset
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger

REQUIRED_COLUMNS = [
    "encounter_id",
    "patient_nbr",
    "race",
    "gender",
    "age",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
    "readmitted",
]

NUMERIC_NON_NEGATIVE_COLS = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
]

VALID_GENDERS = {"Female", "Male", "Unknown/Invalid"}
VALID_AGE_BRACKETS = {
    "[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
    "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"
}


class DataQualityValidator:
    """Validates records, flags violations, and separates rejected records."""

    def __init__(self, run_id: str = "DEFAULT_RUN", source_file: str = "diabetic_data.csv"):
        self.run_id = run_id
        self.source_file = source_file
        self.validation_summary: Dict[str, Any] = {
            "total_input_records": 0,
            "valid_records": 0,
            "rejected_records": 0,
            "rejections_by_reason": {},
            "schema_valid": True,
            "missing_columns": [],
            "unexpected_columns": [],
        }

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validates that all essential columns exist in the DataFrame."""
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        unexpected = [col for col in df.columns if col not in REQUIRED_COLUMNS and not col.startswith(("diag_", "pipeline_", "staged_"))]

        self.validation_summary["missing_columns"] = missing
        self.validation_summary["unexpected_columns"] = unexpected

        if missing:
            logger.error(f"[{self.run_id}] Schema validation failed! Missing required columns: {missing}")
            self.validation_summary["schema_valid"] = False
            return False

        logger.info(f"[{self.run_id}] Schema validation passed. Found all {len(REQUIRED_COLUMNS)} required columns.")
        return True

    def validate_and_filter(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Runs comprehensive validation checks and segregates valid from rejected records.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (valid_df, rejected_df)
        """
        self.validation_summary["total_input_records"] = len(df)
        if not self.validate_schema(df):
            raise ValueError(f"Schema mismatch: missing columns {self.validation_summary['missing_columns']}")

        df_work = df.copy()
        rejection_reasons = pd.Series(index=df_work.index, dtype="object")

        # 1. Null check on critical identifiers
        null_encounter = df_work["encounter_id"].isna() | (df_work["encounter_id"].astype(str).str.strip() == "")
        rejection_reasons[null_encounter] = "MISSING_ENCOUNTER_ID"

        null_patient = df_work["patient_nbr"].isna() | (df_work["patient_nbr"].astype(str).str.strip() == "")
        rejection_reasons[null_patient & rejection_reasons.isna()] = "MISSING_PATIENT_NBR"

        # 2. Duplicate encounter ID check
        duplicate_encounters = df_work.duplicated(subset=["encounter_id"], keep="first")
        rejection_reasons[duplicate_encounters & rejection_reasons.isna()] = "DUPLICATE_ENCOUNTER_ID"

        # 3. Numeric bounds (must be non-negative numbers)
        for num_col in NUMERIC_NON_NEGATIVE_COLS:
            if num_col in df_work.columns:
                val = pd.to_numeric(df_work[num_col], errors="coerce")
                invalid_num = val.isna() | (val < 0)
                rejection_reasons[invalid_num & rejection_reasons.isna()] = f"INVALID_{num_col.upper()}_BOUNDS"

        # 4. Specific category validation (e.g. valid age format if present)
        if "age" in df_work.columns:
            invalid_age = ~df_work["age"].isin(VALID_AGE_BRACKETS) & df_work["age"].notna()
            rejection_reasons[invalid_age & rejection_reasons.isna()] = "INVALID_AGE_BRACKET"

        # Separate valid and rejected
        is_rejected = rejection_reasons.notna()
        valid_df = df_work[~is_rejected].copy()
        rejected_subset = df_work[is_rejected].copy()

        # Build formal rejected record schema
        rejected_records = []
        for idx, row in rejected_subset.iterrows():
            reason = str(rejection_reasons.loc[idx])  # type: ignore[index]
            rejected_records.append({
                "rejection_id": f"REJ_{self.run_id}_{len(rejected_records) + 1:06d}",
                "original_encounter_id": str(row.get("encounter_id", "UNKNOWN")),
                "rejection_reason": reason,
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "pipeline_run_id": self.run_id,
                "source_file": self.source_file,
                "raw_record_snippet": str(row.to_dict())[:500],
            })

        rejected_df = pd.DataFrame(rejected_records)

        # Update summary
        self.validation_summary["valid_records"] = len(valid_df)
        self.validation_summary["rejected_records"] = len(rejected_df)
        if not rejected_df.empty:
            self.validation_summary["rejections_by_reason"] = (
                rejected_df["rejection_reason"].value_counts().to_dict()
            )

        logger.info(
            f"[{self.run_id}] Validation complete: {len(valid_df)} valid records, "
            f"{len(rejected_df)} rejected records."
        )
        return valid_df, rejected_df

    def persist_rejected_records(self, rejected_df: pd.DataFrame) -> Path:
        """Saves rejected records to persistent data/rejected storage."""
        Config.REJECTED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        out_parquet = Config.REJECTED_DATA_DIR / f"rejected_encounters_{self.run_id}.parquet"
        out_csv = Config.REJECTED_DATA_DIR / f"rejected_encounters_{self.run_id}.csv"

        rejected_df.to_parquet(out_parquet, index=False)
        rejected_df.to_csv(out_csv, index=False)
        logger.info(f"[{self.run_id}] Persisted rejected records to {out_parquet} and {out_csv}")
        return out_parquet
