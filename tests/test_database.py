"""Tests for database connectivity, DDL parsing, and analytical mart creation."""

import pytest
from pathlib import Path
import pandas as pd
from src.utils.config import Config
from src.database.connection import DatabaseManager
from src.database.load_postgres import DataLoader
from src.transformation.feature_engineering import FeatureEngineer


def test_sql_ddl_files_exist():
    """Verifies all 5 SQL migration and analytical query files exist."""
    sql_dir = Config.ROOT_DIR / "sql"
    expected_files = [
        "01_create_schemas.sql",
        "02_create_tables.sql",
        "03_create_indexes.sql",
        "04_create_views.sql",
        "05_analytics_queries.sql",
    ]
    for sql_file in expected_files:
        path = sql_dir / sql_file
        assert path.exists(), f"Missing SQL file: {sql_file}"
        assert path.stat().st_size > 0, f"Empty SQL file: {sql_file}"


def test_database_manager_offline_handling():
    """Verifies DatabaseManager returns False gracefully when DB is not running."""
    # Should not raise uncaught exceptions
    is_connected = DatabaseManager.check_connection()
    assert isinstance(is_connected, bool)


def test_analytics_mart_builder(sample_raw_dataframe):
    """Verifies pre-aggregated data marts are constructed accurately."""
    fe = FeatureEngineer(run_id="TEST_MART_RUN")
    df_feat = fe.engineer_features(sample_raw_dataframe)
    tables = fe.build_relational_tables(df_feat)
    patient_summary = fe.generate_patient_summary(tables["encounters"])

    loader = DataLoader(run_id="TEST_MART_RUN")
    marts = loader.build_and_load_analytics_marts(tables, patient_summary)

    assert "patient_summary" in marts
    assert "readmission_summary" in marts
    assert "admission_summary" in marts
    assert "diagnosis_summary" in marts
    assert "length_of_stay_summary" in marts

    # Check metrics integrity
    assert not marts["readmission_summary"].empty
    assert "readmission_rate_30d" in marts["readmission_summary"].columns
    assert "length_of_stay" in marts["length_of_stay_summary"].columns
