"""Pytest fixtures and configuration."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_raw_dataframe():
    """Provides a small, controlled synthetic DataFrame mirroring the UCI dataset."""
    return pd.DataFrame({
        "encounter_id": [101, 102, 103, 104, 105],
        "patient_nbr": [1001, 1002, 1001, 1003, 1004],
        "race": ["Caucasian", "AfricanAmerican", "?", "Hispanic", "Asian"],
        "gender": ["Female", "Male", "Female", "Unknown/Invalid", "Male"],
        "age": ["[50-60)", "[70-80)", "[20-30)", "[40-50)", "[80-90)"],
        "admission_type_id": [1, 2, 3, 1, 2],
        "discharge_disposition_id": [1, 3, 1, 6, 1],
        "admission_source_id": [7, 1, 7, 2, 7],
        "time_in_hospital": [3, 5, 1, 8, 2],
        "num_lab_procedures": [40, 55, 20, 70, 30],
        "num_procedures": [0, 1, 2, 0, 3],
        "num_medications": [10, 15, 6, 22, 12],
        "number_outpatient": [0, 1, 0, 2, 0],
        "number_emergency": [1, 0, 0, 0, 0],
        "number_inpatient": [0, 2, 0, 1, 0],
        "diag_1": ["410", "250.01", "486", "820", "584"],
        "diag_2": ["401", "276", "428", "250.02", "414"],
        "diag_3": ["250.00", "414", "401", "786", "250.6"],
        "number_diagnoses": [9, 7, 5, 9, 8],
        "readmitted": ["<30", ">30", "NO", "<30", "NO"],
    })
