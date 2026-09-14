"""Tests for data quality, schema validation, and rejected records."""

import pytest
import pandas as pd
from src.transformation.validate_data import DataQualityValidator


def test_schema_validation_success(sample_raw_dataframe):
    """Verifies schema check passes when all required columns exist."""
    validator = DataQualityValidator(run_id="TEST_RUN")
    assert validator.validate_schema(sample_raw_dataframe) is True
    assert validator.validation_summary["schema_valid"] is True


def test_schema_validation_failure():
    """Verifies schema check fails when critical columns are missing."""
    df_incomplete = pd.DataFrame({"encounter_id": [1], "age": ["50"]})
    validator = DataQualityValidator(run_id="TEST_RUN")
    assert validator.validate_schema(df_incomplete) is False
    assert "patient_nbr" in validator.validation_summary["missing_columns"]


def test_duplicate_encounter_rejection(sample_raw_dataframe):
    """Verifies duplicate encounters are flagged and rejected."""
    df_with_dups = pd.concat([sample_raw_dataframe, sample_raw_dataframe.iloc[[0]]], ignore_index=True)
    assert len(df_with_dups) == 6

    validator = DataQualityValidator(run_id="TEST_RUN")
    valid_df, rejected_df = validator.validate_and_filter(df_with_dups)

    assert len(valid_df) == 5
    assert len(rejected_df) == 1
    assert "DUPLICATE_ENCOUNTER_ID" in rejected_df["rejection_reason"].values


def test_null_encounter_id_rejection(sample_raw_dataframe):
    """Verifies encounters with missing IDs are rejected."""
    df_corrupt = sample_raw_dataframe.copy()
    df_corrupt.loc[0, "encounter_id"] = None

    validator = DataQualityValidator(run_id="TEST_RUN")
    valid_df, rejected_df = validator.validate_and_filter(df_corrupt)

    assert len(valid_df) == 4
    assert len(rejected_df) == 1
    assert "MISSING_ENCOUNTER_ID" in rejected_df["rejection_reason"].values


def test_negative_numeric_bound_rejection(sample_raw_dataframe):
    """Verifies negative numeric values violate bounds and are rejected."""
    df_corrupt = sample_raw_dataframe.copy()
    df_corrupt.loc[1, "time_in_hospital"] = -5

    validator = DataQualityValidator(run_id="TEST_RUN")
    valid_df, rejected_df = validator.validate_and_filter(df_corrupt)

    assert len(valid_df) == 4
    assert len(rejected_df) == 1
    assert "INVALID_TIME_IN_HOSPITAL_BOUNDS" in rejected_df["rejection_reason"].values
