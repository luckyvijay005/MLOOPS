"""Tests for clinical transformations, missing values, and feature engineering."""

import pytest
import pandas as pd
import numpy as np
from src.transformation.clean_data import clean_missing_values, normalize_readmission
from src.transformation.standardization import categorize_icd9, standardize_attributes
from src.transformation.feature_engineering import (
    generate_surrogate_key,
    map_age_group,
    FeatureEngineer,
)


def test_missing_value_cleaning():
    """Verifies that '?' and placeholder codes are converted to NaN."""
    df = pd.DataFrame({
        "race": ["Caucasian", "?", "Asian", "Unknown/Invalid"],
        "weight": ["?", "[75-100)", "None", "NULL"],
    })
    cleaned = clean_missing_values(df)

    assert pd.isna(cleaned.loc[1, "race"])
    assert pd.isna(cleaned.loc[3, "race"])
    assert pd.isna(cleaned.loc[0, "weight"])
    assert pd.isna(cleaned.loc[2, "weight"])
    assert cleaned.loc[0, "race"] == "Caucasian"


def test_readmission_normalization():
    """Verifies '<30' becomes 1, and '>30'/'NO' become 0."""
    df = pd.DataFrame({"readmitted": ["<30", ">30", "NO", "<30", "0"]})
    norm = normalize_readmission(df)

    assert (norm["readmitted_30d"] == [1, 0, 0, 1, 0]).all()
    assert (norm["readmission_status"] == ["<30", ">30", "NO", "<30", "NO"]).all()


def test_age_group_mapping():
    """Verifies age bracket normalization into 4 standardized groups."""
    assert map_age_group("[10-20)") == "<30"
    assert map_age_group("[20-30)") == "<30"
    assert map_age_group("[30-40)") == "30-50"
    assert map_age_group("[40-50)") == "30-50"
    assert map_age_group("[50-60)") == "50-70"
    assert map_age_group("[60-70)") == "50-70"
    assert map_age_group("[70-80)") == "70+"
    assert map_age_group("[80-90)") == "70+"
    assert map_age_group(None) == "Unknown"


def test_icd9_categorization():
    """Verifies ICD-9 clinical diagnosis category assignment."""
    assert categorize_icd9("250.01") == "Diabetes"
    assert categorize_icd9("410") == "Circulatory"
    assert categorize_icd9("486") == "Respiratory"
    assert categorize_icd9("530") == "Digestive"
    assert categorize_icd9("820") == "Injury and Poisoning"
    assert categorize_icd9("715") == "Musculoskeletal"
    assert categorize_icd9("584") == "Genitourinary"
    assert categorize_icd9("174") == "Neoplasms"
    assert categorize_icd9("?") == "Missing/Unknown"


def test_surrogate_key_properties():
    """Verifies SHA-256 salted surrogate keys are deterministic and hide raw patient numbers."""
    key1 = generate_surrogate_key("12345", salt="test_salt_123")
    key2 = generate_surrogate_key("12345", salt="test_salt_123")
    key3 = generate_surrogate_key("12345", salt="different_salt")

    assert len(key1) == 64
    assert key1 == key2  # Deterministic with same salt
    assert key1 != key3  # Salt sensitivity
    assert "12345" not in key1  # Privacy shield


def test_feature_engineering_pipeline(sample_raw_dataframe):
    """Verifies end-to-end feature engineering and entity splitting."""
    fe = FeatureEngineer(run_id="TEST_RUN")
    df_feat = fe.engineer_features(sample_raw_dataframe)

    assert "patient_nbr" not in df_feat.columns  # Dropped for privacy
    assert "patient_key" in df_feat.columns
    assert "encounter_key" in df_feat.columns
    assert "length_of_stay" in df_feat.columns
    assert "medication_count" in df_feat.columns

    tables = fe.build_relational_tables(df_feat)
    assert "encounters" in tables
    assert "diagnoses" in tables
    assert "admissions" in tables
    assert "readmissions" in tables

    # Check patient summary
    pat_summary = fe.generate_patient_summary(tables["encounters"])
    assert len(pat_summary) == 4  # 4 unique patients in sample_raw_dataframe
    assert "readmission_rate" in pat_summary.columns
