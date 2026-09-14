"""Data loading layer for Streamlit Dashboard.

Supports dual backend:
1. Direct query execution against PostgreSQL analytical schemas (if database is online)
2. Local Parquet cache fallback (if running standalone without active PostgreSQL)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from sqlalchemy import text

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from src.database.connection import DatabaseManager


def load_data_from_db_or_cache() -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Loads curated encounters and analytical summary dataframes.

    Returns:
        Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]: (curated_encounters, analytics_marts)
    """
    is_db_up = DatabaseManager.check_connection()
    df_encounters = None
    marts = {}

    if is_db_up:
        try:
            engine = DatabaseManager.get_engine()
            logger.info("Fetching dashboard data from PostgreSQL...")
            with engine.connect() as conn:
                df_encounters = pd.read_sql(text("SELECT * FROM curated.encounters;"), con=conn)
                marts["patient_summary"] = pd.read_sql(text("SELECT * FROM analytics.patient_summary;"), con=conn)
                marts["readmission_summary"] = pd.read_sql(text("SELECT * FROM analytics.readmission_summary;"), con=conn)
                marts["admission_summary"] = pd.read_sql(text("SELECT * FROM analytics.admission_summary;"), con=conn)
                marts["diagnosis_summary"] = pd.read_sql(text("SELECT * FROM analytics.diagnosis_summary;"), con=conn)
                marts["length_of_stay_summary"] = pd.read_sql(text("SELECT * FROM analytics.length_of_stay_summary;"), con=conn)
            return df_encounters, marts
        except Exception as exc:
            logger.warning(f"Failed to query PostgreSQL for dashboard: {exc}. Falling back to Parquet.")

    # Fallback to local Parquet cache
    enc_file = Config.CLEANED_DATA_DIR / "curated_encounters_latest.parquet"
    if enc_file.exists():
        logger.info(f"Loading dashboard data from local cache: {enc_file}")
        df_encounters = pd.read_parquet(enc_file)
    else:
        # Check if sample dataset exists to build a preview dataframe
        sample_file = Config.SAMPLE_DATA_DIR / "synthetic_diabetic_data.csv"
        if sample_file.exists():
            from src.transformation.clean_data import clean_encounter_data
            from src.transformation.standardization import standardize_attributes
            from src.transformation.feature_engineering import FeatureEngineer
            df_raw = pd.read_csv(sample_file)
            df_clean = clean_encounter_data(df_raw)
            df_std = standardize_attributes(df_clean)
            fe = FeatureEngineer()
            df_feat = fe.engineer_features(df_std)
            tables = fe.build_relational_tables(df_feat)
            fe.persist_curated_data(tables)
            df_encounters = tables["encounters"]
        else:
            # Empty fallback schema to prevent crash before pipeline run
            df_encounters = pd.DataFrame(columns=[
                "encounter_key", "patient_key", "age_group", "gender", "race",
                "admission_type", "discharge_disposition", "admission_source",
                "time_in_hospital", "num_lab_procedures", "num_procedures",
                "num_medications", "number_diagnoses", "readmission_status",
                "readmitted_30d"
            ])

    # Load summary marts from parquet
    for name in ["patient_summary", "readmission_summary", "admission_summary", "diagnosis_summary", "length_of_stay_summary"]:
        path = Config.CLEANED_DATA_DIR / f"analytics_{name}_latest.parquet"
        if path.exists():
            marts[name] = pd.read_parquet(path)
        else:
            marts[name] = pd.DataFrame()

    return df_encounters, marts


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes executive KPIs from an encounters DataFrame."""
    if df.empty:
        return {
            "total_encounters": 0,
            "unique_patients": 0,
            "readmission_rate_30d": 0.0,
            "avg_length_of_stay": 0.0,
            "avg_medications": 0.0,
        }

    total_enc = len(df)
    unique_pat = df["patient_key"].nunique() if "patient_key" in df.columns else total_enc
    readm_30 = df["readmitted_30d"].mean() * 100 if "readmitted_30d" in df.columns else 0.0
    avg_los = df["time_in_hospital"].mean() if "time_in_hospital" in df.columns else 0.0
    avg_meds = df["num_medications"].mean() if "num_medications" in df.columns else 0.0

    return {
        "total_encounters": total_enc,
        "unique_patients": unique_pat,
        "readmission_rate_30d": round(readm_30, 2),
        "avg_length_of_stay": round(avg_los, 2),
        "avg_medications": round(avg_meds, 2),
    }
