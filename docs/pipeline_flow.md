# ETL Pipeline Workflow & Orchestration Flow

## 1. Overview
The Hospital Readmission Analytics ETL pipeline can be executed in two interchangeable execution modes:
1. **Apache Airflow DAG (`hospital_readmission_etl`):** Scheduled, directed acyclic graph orchestrated via the Airflow scheduler/webserver or Docker container.
2. **Standalone Pipeline Runner (`scripts/run_pipeline.py`):** Pure-Python CLI runner implementing the identical 12-stage logic with zero external orchestration dependencies, ideal for local Windows development.

---

## 2. The 12 Logical Pipeline Tasks

| Stage | Task ID | Execution Function | Input Data | Output Artifact | Idempotency Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `check_source` | `download_and_extract_dataset()` | Network / Local | `data/raw/diabetic_data.csv` | Re-uses existing valid file if present |
| **2** | `ingest_raw_data` | `IngestionManager.verify_and_audit_raw()` | `diabetic_data.csv` | Ingestion metadata, Checksum | Appends run-keyed record to audit log |
| **3** | `validate_schema` | `DataQualityValidator.validate_schema()` | Staging Preview | Schema validation report | Deterministic column inspection |
| **4** | `load_staging` | `IngestionManager.stage_dataset()` | Raw CSV | `staging.diabetic_encounters` | Truncates & repopulates staging table |
| **5** | `clean_data` | `clean_encounter_data()` | Staged DataFrame | Cleaned DataFrame | Pure function mapping `'?'` to `NULL` |
| **6** | `validate_cleaned_data` | `DataQualityValidator.validate_and_filter()` | Standardized Data | Valid vs Rejected split | Pure validation rules filter |
| **7** | `generate_rejected_records` | `DataLoader.load_rejected_table()` | Rejected records | `rejected.encounters` | Appends rejected records with `run_id` |
| **8** | `engineer_features` | `FeatureEngineer.engineer_features()` | Valid records | Privacy-shielded features | Salted SHA-256 surrogate hashing |
| **9** | `create_analytical_tables` | `FeatureEngineer.build_relational_tables()` | Engineered features | Encounters, Diagnoses, Admissions, Readmissions | Generates normalized relational entities |
| **10** | `load_postgresql` | `DataLoader.load_curated_tables()` | Curated entities | PostgreSQL `curated.*` | Truncates and reloads curated schema |
| **11** | `run_quality_checks` | Post-load assertion checks | Curated tables | Assertion status | Verifies uniqueness of `encounter_key` |
| **12** | `generate_pipeline_summary` | Run summary reporter | Pipeline metrics | `reports/pipeline_run_summary_*.json` | Generates immutable run summary log |

---

## 3. Execution Idempotency & Fault Tolerance
- **Rerun Safety:** Rerunning the pipeline on the same or updated data overwrites staging/curated tables cleanly or indexes by `pipeline_run_id`. No duplicate records are created.
- **Fail-Safe Processing:** If a critical error occurs (e.g. corrupt CSV or database timeout), the error is caught, formatted into the summary report with exit code 1, and logged to `logs/pipeline.log`.
- **Database Decoupling:** If PostgreSQL is offline, all curated and analytical tables are persisted to `data/cleaned/*.parquet` so the Streamlit dashboard remains fully operational.
