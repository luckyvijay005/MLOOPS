"""Data cleaning module.

Provides deterministic cleaning operations:
- Maps dataset-specific missing value indicators ('?', 'Unknown/Invalid', etc.) to explicit NULLs
- Strips whitespace and standardizes casing
- Normalizes readmission target to '<30', '>30', 'NO' and creates readmitted_30d binary flag
"""

import sys
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger

# Missing value representations known in the UCI Diabetes dataset
MISSING_REPRESENTATIONS = [
    "?",
    "Unknown/Invalid",
    "Not Mapped",
    "Not Available",
    "NULL",
    "None",
    "",
]


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces missing code representations with np.nan while preserving raw staging data."""
    df_cleaned = df.copy()

    # Columns where specific strings indicate missing values
    for col in df_cleaned.columns:
        if df_cleaned[col].dtype == object or pd.api.types.is_string_dtype(df_cleaned[col]):
            # Strip whitespace
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
            # Replace missing representations with NaN
            df_cleaned[col] = df_cleaned[col].replace(MISSING_REPRESENTATIONS, np.nan)

    return df_cleaned


def normalize_readmission(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes readmission values and computes readmitted_30d binary target.

    In the UCI dataset:
      - '<30': Encounter was followed by readmission within 30 days -> readmitted_30d = 1
      - '>30': Readmission occurred after 30 days -> readmitted_30d = 0
      - 'NO': No readmission observed -> readmitted_30d = 0
    """
    df_norm = df.copy()

    # Normalize status column
    status = df_norm["readmitted"].fillna("NO").astype(str).str.strip()
    # Map valid codes
    valid_status_map = {
        "<30": "<30",
        ">30": ">30",
        "NO": "NO",
        "0": "NO",
        "1": "<30",
    }
    df_norm["readmission_status"] = status.map(lambda s: valid_status_map.get(str(s), "NO"))

    # Compute binary readmission within 30 days indicator
    df_norm["readmitted_30d"] = (df_norm["readmission_status"] == "<30").astype(int)

    return df_norm


def clean_encounter_data(df: pd.DataFrame) -> pd.DataFrame:
    """Executes full cleaning workflow on raw/staged DataFrame."""
    logger.info(f"Starting data cleaning on {len(df)} records...")
    df_clean = clean_missing_values(df)
    df_clean = normalize_readmission(df_clean)
    logger.info("Data cleaning completed successfully.")
    return df_clean
