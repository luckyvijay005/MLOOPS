"""Database Bulk Loading and Analytical Data Mart Builder.

Loads staged, rejected, and curated tables into PostgreSQL and populates
analytical data marts. Also persists local cache for high-availability dashboard usage.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np
from sqlalchemy import text

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from src.database.connection import DatabaseManager


class DataLoader:
    """Handles bulk table persistence and analytical data mart calculation."""

    def __init__(self, run_id: str = "DEFAULT_RUN"):
        self.run_id = run_id
        self.engine = DatabaseManager.get_engine() if DatabaseManager.check_connection() else None

    def log_ingestion_metadata(self, metadata: dict) -> None:
        """Records raw file ingestion metrics into metadata.etl_ingestion_log."""
        if not metadata:
            return

        df_meta = pd.DataFrame([{
            "source_name": metadata.get("source_name", "UCI"),
            "source_file": metadata.get("source_file", "diabetic_data.csv"),
            "extraction_timestamp": metadata.get("extraction_timestamp"),
            "file_checksum": metadata.get("file_checksum", ""),
            "row_count": metadata.get("row_count", 0),
            "column_count": metadata.get("column_count", 0),
            "status": metadata.get("status", "SUCCESS"),
            "error_message": metadata.get("error_message"),
            "pipeline_run_id": metadata.get("pipeline_run_id", self.run_id),
        }])

        # Save locally
        audit_csv = Config.REPORTS_DIR / f"ingestion_audit_{self.run_id}.csv"
        df_meta.to_csv(audit_csv, index=False)

        if self.engine:
            try:
                with self.engine.begin() as conn:
                    df_meta.to_sql(
                        name="etl_ingestion_log",
                        con=conn,
                        schema=Config.SCHEMA_METADATA,
                        if_exists="append",
                        index=False,
                    )
                logger.info(f"[{self.run_id}] Logged ingestion metadata to database.")
            except Exception as exc:
                logger.warning(f"Could not write metadata to PostgreSQL: {exc}")

    def load_staging_table(self, df_staging: pd.DataFrame) -> None:
        """Loads staging dataset into staging.diabetic_encounters."""
        if self.engine:
            try:
                logger.info(f"[{self.run_id}] Loading {len(df_staging)} rows into staging.diabetic_encounters...")
                # Truncate existing staging data for clean idempotent run
                with self.engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE staging.diabetic_encounters;"))
                    df_staging.to_sql(
                        name="diabetic_encounters",
                        con=conn,
                        schema=Config.SCHEMA_STAGING,
                        if_exists="append",
                        index=False,
                        chunksize=5000,
                        method="multi",
                    )
                logger.info(f"[{self.run_id}] Staging table loaded successfully.")
            except Exception as exc:
                logger.warning(f"Could not load staging to PostgreSQL: {exc}")

    def load_rejected_table(self, df_rejected: pd.DataFrame) -> None:
        """Loads rejected records into rejected.encounters."""
        if df_rejected.empty:
            return

        if self.engine:
            try:
                logger.info(f"[{self.run_id}] Loading {len(df_rejected)} records into rejected.encounters...")
                df_to_load = df_rejected.drop(columns=["rejection_id"], errors="ignore")
                with self.engine.begin() as conn:
                    df_to_load.to_sql(
                        name="encounters",
                        con=conn,
                        schema=Config.SCHEMA_REJECTED,
                        if_exists="append",
                        index=False,
                        chunksize=5000,
                        method="multi",
                    )
                logger.info(f"[{self.run_id}] Rejected records loaded to database.")
            except Exception as exc:
                logger.warning(f"Could not load rejected records to PostgreSQL: {exc}")

    def load_curated_tables(self, tables: Dict[str, pd.DataFrame]) -> None:
        """Loads normalized entities into curated schema."""
        if not self.engine:
            logger.info("PostgreSQL not connected; curated tables saved locally in Parquet format.")
            return

        try:
            with self.engine.begin() as conn:
                logger.info(f"[{self.run_id}] Truncating previous curated records for idempotent load...")
                conn.execute(text("TRUNCATE TABLE curated.readmissions, curated.admissions, curated.diagnoses, curated.encounters CASCADE;"))

                # 1. Curated Encounters
                logger.info(f"[{self.run_id}] Loading {len(tables['encounters'])} rows to curated.encounters...")
                tables["encounters"].to_sql(
                    name="encounters",
                    con=conn,
                    schema=Config.SCHEMA_CURATED,
                    if_exists="append",
                    index=False,
                    chunksize=5000,
                    method="multi",
                )

                # 2. Curated Diagnoses
                if not tables["diagnoses"].empty:
                    logger.info(f"[{self.run_id}] Loading {len(tables['diagnoses'])} rows to curated.diagnoses...")
                    tables["diagnoses"].to_sql(
                        name="diagnoses",
                        con=conn,
                        schema=Config.SCHEMA_CURATED,
                        if_exists="append",
                        index=False,
                        chunksize=5000,
                        method="multi",
                    )

                # 3. Curated Admissions
                if not tables["admissions"].empty:
                    logger.info(f"[{self.run_id}] Loading {len(tables['admissions'])} rows to curated.admissions...")
                    tables["admissions"].to_sql(
                        name="admissions",
                        con=conn,
                        schema=Config.SCHEMA_CURATED,
                        if_exists="append",
                        index=False,
                        chunksize=5000,
                        method="multi",
                    )

                # 4. Curated Readmissions
                if not tables["readmissions"].empty:
                    logger.info(f"[{self.run_id}] Loading {len(tables['readmissions'])} rows to curated.readmissions...")
                    tables["readmissions"].to_sql(
                        name="readmissions",
                        con=conn,
                        schema=Config.SCHEMA_CURATED,
                        if_exists="append",
                        index=False,
                        chunksize=5000,
                        method="multi",
                    )

            logger.info(f"[{self.run_id}] Curated tables successfully loaded into PostgreSQL.")
        except Exception as exc:
            logger.error(f"Error loading curated tables to PostgreSQL: {exc}")
            raise

    def build_and_load_analytics_marts(
        self,
        tables: Dict[str, pd.DataFrame],
        patient_summary: pd.DataFrame,
    ) -> Dict[str, pd.DataFrame]:
        """Calculates and persists pre-aggregated analytical data marts."""
        logger.info(f"[{self.run_id}] Building analytical data marts...")
        df_enc = tables["encounters"]
        df_diag = tables["diagnoses"]
        df_adm = tables["admissions"]

        # 1. Readmission Summary (Age x Gender x Race x Admission Type)
        readm_grp = df_enc.groupby(["age_group", "gender", "race", "admission_type"]).agg(
            total_encounters=("encounter_key", "count"),
            readmitted_30d_count=("readmitted_30d", "sum"),
            readmission_rate_30d=("readmitted_30d", "mean"),
            readmission_over30d_count=("readmission_status", lambda x: (x == ">30").sum()),
            no_readmission_count=("readmission_status", lambda x: (x == "NO").sum()),
            avg_length_of_stay=("time_in_hospital", "mean"),
        ).reset_index()
        readm_grp["readmission_rate_30d"] = readm_grp["readmission_rate_30d"].round(4)
        readm_grp["avg_length_of_stay"] = readm_grp["avg_length_of_stay"].round(2)

        # 2. Admission Summary (Admission Type x Source x Disposition)
        adm_grp = df_adm.merge(
            df_enc[["encounter_key", "readmitted_30d"]], on="encounter_key", how="left"
        ).groupby(["admission_type", "admission_source", "discharge_disposition"]).agg(
            total_encounters=("encounter_key", "count"),
            readmitted_30d_count=("readmitted_30d", "sum"),
            readmission_rate_30d=("readmitted_30d", "mean"),
            avg_length_of_stay=("length_of_stay", "mean"),
        ).reset_index()
        adm_grp["readmission_rate_30d"] = adm_grp["readmission_rate_30d"].round(4)
        adm_grp["avg_length_of_stay"] = adm_grp["avg_length_of_stay"].round(2)

        # 3. Diagnosis Summary (Category x Position)
        diag_grp = df_diag.merge(
            df_enc[["encounter_key", "readmitted_30d"]], on="encounter_key", how="left"
        ).groupby(["diagnosis_category", "diagnosis_position"]).agg(
            total_diagnoses=("diagnosis_key", "count"),
            readmitted_30d_count=("readmitted_30d", "sum"),
            readmission_rate_30d=("readmitted_30d", "mean"),
        ).reset_index()
        diag_grp["readmission_rate_30d"] = diag_grp["readmission_rate_30d"].round(4)

        # 4. Length of Stay Summary
        los_grp = df_enc.groupby("time_in_hospital").agg(
            total_encounters=("encounter_key", "count"),
            readmitted_30d_count=("readmitted_30d", "sum"),
            readmission_rate_30d=("readmitted_30d", "mean"),
            avg_medications=("num_medications", "mean"),
            avg_diagnoses=("number_diagnoses", "mean"),
        ).reset_index().rename(columns={"time_in_hospital": "length_of_stay"})
        los_grp["readmission_rate_30d"] = los_grp["readmission_rate_30d"].round(4)
        los_grp["avg_medications"] = los_grp["avg_medications"].round(2)
        los_grp["avg_diagnoses"] = los_grp["avg_diagnoses"].round(2)

        marts = {
            "patient_summary": patient_summary,
            "readmission_summary": readm_grp,
            "admission_summary": adm_grp,
            "diagnosis_summary": diag_grp,
            "length_of_stay_summary": los_grp,
        }

        # Persist local Parquet cache for Streamlit offline support
        for mart_name, mart_df in marts.items():
            mart_file = Config.CLEANED_DATA_DIR / f"analytics_{mart_name}_{self.run_id}.parquet"
            latest_mart = Config.CLEANED_DATA_DIR / f"analytics_{mart_name}_latest.parquet"
            mart_df.to_parquet(mart_file, index=False)
            mart_df.to_parquet(latest_mart, index=False)

        # Persist to PostgreSQL if connected
        if self.engine:
            try:
                with self.engine.begin() as conn:
                    conn.execute(text(
                        "TRUNCATE TABLE analytics.patient_summary, analytics.readmission_summary, "
                        "analytics.admission_summary, analytics.diagnosis_summary, "
                        "analytics.length_of_stay_summary CASCADE;"
                    ))

                    for mart_name, mart_df in marts.items():
                        logger.info(f"[{self.run_id}] Loading {len(mart_df)} rows to analytics.{mart_name}...")
                        mart_df.to_sql(
                            name=mart_name,
                            con=conn,
                            schema=Config.SCHEMA_ANALYTICS,
                            if_exists="append",
                            index=False,
                            chunksize=5000,
                            method="multi",
                        )
                logger.info(f"[{self.run_id}] Analytics data marts loaded into PostgreSQL.")
            except Exception as exc:
                logger.warning(f"Could not load data marts to PostgreSQL: {exc}")

        return marts
