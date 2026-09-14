"""End-to-End ETL Pipeline Runner.

Orchestrates all 12 stages of the Hospital Readmission Analytics pipeline:
1. Check Source & Download Verification
2. Ingest Raw Data & Compute Audit Checksums
3. Validate Staging Schema
4. Load Staging Layer
5. Clean Data & Map Missing Values
6. Standardize Clinical Fields (Lookups & ICD-9 Categorization)
7. Validate Cleaned Data & Segregate Rejected Records
8. Feature Engineering & Privacy Shield (Surrogate Hashing)
9. Normalize Relational Entities (Encounters, Diagnoses, Admissions, Readmissions)
10. Build Analytical Data Marts (Patient Summary, Readmission Summary, etc.)
11. Load PostgreSQL / Local High-Availability Cache
12. Generate Structured Pipeline Execution Summary Report
"""

import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from src.ingestion.download_dataset import download_and_extract_dataset
from src.ingestion.ingest import IngestionManager
from src.transformation.clean_data import clean_encounter_data
from src.transformation.standardization import standardize_attributes
from src.transformation.validate_data import DataQualityValidator
from src.transformation.feature_engineering import FeatureEngineer
from src.database.connection import DatabaseManager
from src.database.create_schema import initialize_database
from src.database.load_postgres import DataLoader


def run_etl_pipeline(dataset_path: Path | None = None, run_id: str | None = None) -> dict:
    """Executes the complete hospital readmission data engineering pipeline."""
    start_time = datetime.now(timezone.utc)
    pipeline_run_id = run_id or start_time.strftime("RUN_%Y%m%d_%H%M%S")

    logger.info("=" * 80)
    logger.info(f"STARTING HOSPITAL READMISSION PIPELINE: {pipeline_run_id}")
    logger.info("=" * 80)

    summary: dict[str, Any] = {
        "pipeline_run_id": pipeline_run_id,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "input_dataset_path": str(dataset_path or Config.DATASET_PATH),
        "input_rows": 0,
        "staged_rows": 0,
        "cleaned_rows": 0,
        "rejected_rows": 0,
        "curated_encounters": 0,
        "curated_diagnoses": 0,
        "curated_admissions": 0,
        "curated_readmissions": 0,
        "unique_patients": 0,
        "duplicate_records_found": 0,
        "null_or_bound_violations": 0,
        "rejection_breakdown": {},
        "database_connected": False,
        "status": "IN_PROGRESS",
        "error_message": None,
    }

    try:
        # Step 1: Check source & download if missing
        active_raw_path = dataset_path or Config.DATASET_PATH
        if not active_raw_path.exists():
            logger.info(f"Raw file not found at {active_raw_path}. Attempting acquisition...")
            active_raw_path, _ = download_and_extract_dataset()

        summary["input_dataset_path"] = str(active_raw_path)

        # Step 2: Ingest raw data & verify metadata
        ingestion_mgr = IngestionManager(raw_path=active_raw_path, run_id=pipeline_run_id)
        raw_metadata = ingestion_mgr.verify_and_audit_raw()
        summary["input_rows"] = raw_metadata["row_count"]

        # Step 3 & 4: Load Staging Layer
        df_staged = ingestion_mgr.stage_dataset()
        summary["staged_rows"] = len(df_staged)

        # Step 5: Clean Data & map missing representations
        df_cleaned = clean_encounter_data(df_staged)
        summary["cleaned_rows"] = len(df_cleaned)

        # Step 6: Standardize lookups and categorize ICD-9 codes
        df_standardized = standardize_attributes(df_cleaned)

        # Step 7: Validate Data Quality & separate rejected encounters
        validator = DataQualityValidator(run_id=pipeline_run_id, source_file=active_raw_path.name)
        df_valid, df_rejected = validator.validate_and_filter(df_standardized)
        
        summary["rejected_rows"] = len(df_rejected)
        summary["rejection_breakdown"] = validator.validation_summary.get("rejections_by_reason", {})
        summary["duplicate_records_found"] = summary["rejection_breakdown"].get("DUPLICATE_ENCOUNTER_ID", 0)
        
        if not df_rejected.empty:
            validator.persist_rejected_records(df_rejected)

        # Step 8: Feature Engineering & Privacy Shield
        feat_eng = FeatureEngineer(run_id=pipeline_run_id)
        df_featured = feat_eng.engineer_features(df_valid)

        # Step 9: Normalize relational entities
        tables = feat_eng.build_relational_tables(df_featured)
        feat_eng.persist_curated_data(tables)

        summary["curated_encounters"] = len(tables["encounters"])
        summary["curated_diagnoses"] = len(tables["diagnoses"])
        summary["curated_admissions"] = len(tables["admissions"])
        summary["curated_readmissions"] = len(tables["readmissions"])

        # Step 10: Generate Patient Summary Analytical Mart
        patient_summary = feat_eng.generate_patient_summary(tables["encounters"])
        summary["unique_patients"] = len(patient_summary)

        # Step 11: Database Schema & Bulk Loading
        data_loader = DataLoader(run_id=pipeline_run_id)
        data_loader.log_ingestion_metadata(raw_metadata)

        is_db_up = DatabaseManager.check_connection()
        summary["database_connected"] = is_db_up
        if is_db_up:
            logger.info("Initializing PostgreSQL schemas and tables...")
            initialize_database()
            data_loader.load_staging_table(df_staged)
            data_loader.load_rejected_table(df_rejected)
            data_loader.load_curated_tables(tables)
        else:
            logger.info("PostgreSQL is offline. Using local high-availability Parquet analytics cache.")

        # Build analytical data marts (both for PostgreSQL and local Parquet)
        data_loader.build_and_load_analytics_marts(tables, patient_summary)

        # Step 12: Finalize Summary Report
        end_time = datetime.now(timezone.utc)
        summary["end_time"] = end_time.isoformat()
        summary["duration_seconds"] = round((end_time - start_time).total_seconds(), 2)
        summary["status"] = "SUCCESS"

        logger.info("=" * 80)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY in {summary['duration_seconds']}s")
        logger.info(f"Curated Encounters: {summary['curated_encounters']} | Rejected: {summary['rejected_rows']}")
        logger.info("=" * 80)

    except Exception as exc:
        end_time = datetime.now(timezone.utc)
        summary["end_time"] = end_time.isoformat()
        summary["status"] = "FAILED"
        summary["error_message"] = str(exc)
        logger.error(f"Pipeline execution failed: {exc}", exc_info=True)
        raise
    finally:
        # Write structured summary report to reports/
        Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        summary_json_path = Config.REPORTS_DIR / f"pipeline_run_summary_{pipeline_run_id}.json"
        summary_md_path = Config.REPORTS_DIR / f"pipeline_run_summary_{pipeline_run_id}.md"

        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(summary_md_path, "w", encoding="utf-8") as f:
            f.write(f"# Pipeline Execution Summary: {pipeline_run_id}\n\n")
            f.write(f"- **Status**: `{summary['status']}`\n")
            f.write(f"- **Start Time**: `{summary['start_time']}`\n")
            f.write(f"- **End Time**: `{summary['end_time']}`\n")
            f.write(f"- **Duration**: `{summary.get('duration_seconds', 0)} seconds`\n")
            f.write(f"- **Input Dataset**: `{summary['input_dataset_path']}`\n")
            f.write(f"- **Input Rows**: `{summary['input_rows']:,}`\n")
            f.write(f"- **Curated Encounters**: `{summary['curated_encounters']:,}`\n")
            f.write(f"- **Unique Patients**: `{summary['unique_patients']:,}`\n")
            f.write(f"- **Rejected Records**: `{summary['rejected_rows']:,}`\n")
            f.write(f"- **Database Loaded**: `{summary['database_connected']}`\n\n")
            if summary.get("rejection_breakdown"):
                f.write("### Rejection Reason Breakdown\n\n")
                f.write("| Reason | Count |\n| --- | --- |\n")
                for reason, count in summary["rejection_breakdown"].items():
                    f.write(f"| `{reason}` | {count} |\n")

        logger.info(f"Run summary written to: {summary_json_path} and {summary_md_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hospital Readmission ETL Pipeline Runner")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=None,
        help="Path to raw CSV dataset (defaults to DATASET_PATH in .env)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Custom run ID for tracking",
    )
    args = parser.parse_args()
    run_etl_pipeline(dataset_path=args.dataset_path, run_id=args.run_id)
