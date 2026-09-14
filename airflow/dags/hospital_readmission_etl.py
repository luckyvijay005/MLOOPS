"""Apache Airflow DAG: Hospital Readmission ETL Pipeline.

Defines a 12-task idempotent workflow orchestrating raw ingestion,
staging, data quality validation, clinical feature engineering,
PostgreSQL loading, and analytical data mart generation.
"""

from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add project root to sys.path so tasks can import src modules
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Airflow imports with safe fallback for static testing
try:
    from airflow import DAG  # type: ignore
    from airflow.operators.python import PythonOperator  # type: ignore
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    # Mock DAG and PythonOperator for standalone linting/testing
    class DAG:
        def __init__(self, *args, **kwargs):
            self.dag_id = args[0] if args else kwargs.get("dag_id", "")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    class PythonOperator:
        def __init__(self, task_id, python_callable, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable
        def __rshift__(self, other):
            return other

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

# Default task arguments
default_args = {
    "owner": "hospital_data_engineering",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


# Task Callables
def task_check_source(**kwargs):
    logger.info("Airflow Task: check_source starting...")
    data_path, mapping_path = download_and_extract_dataset()
    logger.info(f"Source verified at: {data_path} and {mapping_path}")
    return str(data_path)


def task_ingest_raw_data(**kwargs):
    logger.info("Airflow Task: ingest_raw_data starting...")
    ti = kwargs.get("ti")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    mgr = IngestionManager(run_id=run_id)
    meta = mgr.verify_and_audit_raw()
    return meta


def task_validate_schema(**kwargs):
    logger.info("Airflow Task: validate_schema starting...")
    mgr = IngestionManager()
    df_staged = mgr.stage_dataset()
    validator = DataQualityValidator()
    if not validator.validate_schema(df_staged):
        raise ValueError("Schema validation check failed!")
    logger.info("Schema validation successful.")


def task_load_staging(**kwargs):
    logger.info("Airflow Task: load_staging starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    mgr = IngestionManager(run_id=run_id)
    df_staged = mgr.stage_dataset()
    loader = DataLoader(run_id=run_id)
    loader.load_staging_table(df_staged)


def task_clean_data(**kwargs):
    logger.info("Airflow Task: clean_data starting...")
    mgr = IngestionManager()
    df_staged = mgr.stage_dataset()
    df_cleaned = clean_encounter_data(df_staged)
    df_standardized = standardize_attributes(df_cleaned)
    temp_clean_path = Config.CLEANED_DATA_DIR / "temp_standardized.parquet"
    df_standardized.to_parquet(temp_clean_path, index=False)
    return str(temp_clean_path)


def task_validate_cleaned_data(**kwargs):
    logger.info("Airflow Task: validate_cleaned_data starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    temp_clean_path = Config.CLEANED_DATA_DIR / "temp_standardized.parquet"
    import pandas as pd
    df_std = pd.read_parquet(temp_clean_path)
    validator = DataQualityValidator(run_id=run_id)
    df_valid, df_rejected = validator.validate_and_filter(df_std)
    df_valid.to_parquet(Config.CLEANED_DATA_DIR / "temp_valid.parquet", index=False)
    if not df_rejected.empty:
        validator.persist_rejected_records(df_rejected)
    return len(df_valid)


def task_generate_rejected_records(**kwargs):
    logger.info("Airflow Task: generate_rejected_records starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    loader = DataLoader(run_id=run_id)
    rej_file = Config.REJECTED_DATA_DIR / f"rejected_encounters_{run_id}.parquet"
    if rej_file.exists():
        import pandas as pd
        df_rej = pd.read_parquet(rej_file)
        loader.load_rejected_table(df_rej)
    logger.info("Rejected records persisted.")


def task_engineer_features(**kwargs):
    logger.info("Airflow Task: engineer_features starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    import pandas as pd
    df_valid = pd.read_parquet(Config.CLEANED_DATA_DIR / "temp_valid.parquet")
    feat_eng = FeatureEngineer(run_id=run_id)
    df_featured = feat_eng.engineer_features(df_valid)
    tables = feat_eng.build_relational_tables(df_featured)
    feat_eng.persist_curated_data(tables)
    return len(df_featured)


def task_create_analytical_tables(**kwargs):
    logger.info("Airflow Task: create_analytical_tables starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    import pandas as pd
    tables = {
        "encounters": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_encounters_{run_id}.parquet"),
        "diagnoses": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_diagnoses_{run_id}.parquet"),
        "admissions": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_admissions_{run_id}.parquet"),
        "readmissions": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_readmissions_{run_id}.parquet"),
    }
    feat_eng = FeatureEngineer(run_id=run_id)
    patient_summary = feat_eng.generate_patient_summary(tables["encounters"])
    loader = DataLoader(run_id=run_id)
    loader.build_and_load_analytics_marts(tables, patient_summary)


def task_load_postgresql(**kwargs):
    logger.info("Airflow Task: load_postgresql starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    if DatabaseManager.check_connection():
        initialize_database()
        import pandas as pd
        tables = {
            "encounters": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_encounters_{run_id}.parquet"),
            "diagnoses": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_diagnoses_{run_id}.parquet"),
            "admissions": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_admissions_{run_id}.parquet"),
            "readmissions": pd.read_parquet(Config.CLEANED_DATA_DIR / f"curated_readmissions_{run_id}.parquet"),
        }
        loader = DataLoader(run_id=run_id)
        loader.load_curated_tables(tables)
    else:
        logger.warning("PostgreSQL unreachable; relying on Parquet storage.")


def task_run_quality_checks(**kwargs):
    logger.info("Airflow Task: run_quality_checks starting...")
    import pandas as pd
    latest_enc = Config.CLEANED_DATA_DIR / "curated_encounters_latest.parquet"
    if not latest_enc.exists():
        raise FileNotFoundError("Curated encounters table missing!")
    df = pd.read_parquet(latest_enc)
    assert len(df) > 0, "Curated encounters table is empty!"
    assert df["encounter_key"].nunique() == len(df), "Encounter key uniqueness check failed!"
    assert df["readmitted_30d"].isin([0, 1]).all(), "Readmitted binary column bound check failed!"
    logger.info("All post-load quality checks passed.")


def task_generate_pipeline_summary(**kwargs):
    logger.info("Airflow Task: generate_pipeline_summary starting...")
    run_id = kwargs.get("run_id", "AIRFLOW_RUN")
    logger.info(f"Pipeline run {run_id} completed successfully.")


# Define DAG
with DAG(
    dag_id="hospital_readmission_etl",
    default_args=default_args,
    description="Hospital Readmission Analytics ETL Pipeline",
    schedule_interval=None,
    catchup=False,
    tags=["healthcare", "etl", "readmission", "mlops-part1"],
) as dag:

    t1 = PythonOperator(task_id="check_source", python_callable=task_check_source)
    t2 = PythonOperator(task_id="ingest_raw_data", python_callable=task_ingest_raw_data)
    t3 = PythonOperator(task_id="validate_schema", python_callable=task_validate_schema)
    t4 = PythonOperator(task_id="load_staging", python_callable=task_load_staging)
    t5 = PythonOperator(task_id="clean_data", python_callable=task_clean_data)
    t6 = PythonOperator(task_id="validate_cleaned_data", python_callable=task_validate_cleaned_data)
    t7 = PythonOperator(task_id="generate_rejected_records", python_callable=task_generate_rejected_records)
    t8 = PythonOperator(task_id="engineer_features", python_callable=task_engineer_features)
    t9 = PythonOperator(task_id="create_analytical_tables", python_callable=task_create_analytical_tables)
    t10 = PythonOperator(task_id="load_postgresql", python_callable=task_load_postgresql)
    t11 = PythonOperator(task_id="run_quality_checks", python_callable=task_run_quality_checks)
    t12 = PythonOperator(task_id="generate_pipeline_summary", python_callable=task_generate_pipeline_summary)

    # Idempotent Linear & Branching Dependencies
    t1 >> t2 >> t3 >> t4 >> t5 >> t6
    t6 >> t7
    t6 >> t8 >> t9 >> t10 >> t11 >> t12
    t7 >> t10
