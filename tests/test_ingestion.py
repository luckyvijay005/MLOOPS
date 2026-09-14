"""Tests for ingestion and raw layer verification."""

import pytest
from pathlib import Path
import pandas as pd
from src.ingestion.ingest import IngestionManager, compute_sha256
from scripts.generate_sample_data import generate_synthetic_dataset


def test_synthetic_data_generation(tmp_path):
    """Verifies that the synthetic data generator produces valid schema."""
    out_file = tmp_path / "test_synthetic.csv"
    generate_synthetic_dataset(num_records=50, output_path=out_file)

    assert out_file.exists()
    df = pd.read_csv(out_file)
    assert len(df) == 50
    assert "encounter_id" in df.columns
    assert "patient_nbr" in df.columns
    assert "readmitted" in df.columns


def test_sha256_checksum(tmp_path):
    """Verifies cryptographic hash computation consistency."""
    dummy_file = tmp_path / "sample.txt"
    dummy_file.write_text("Healthcare Analytics Test 2024", encoding="utf-8")

    checksum1 = compute_sha256(dummy_file)
    checksum2 = compute_sha256(dummy_file)

    assert len(checksum1) == 64
    assert checksum1 == checksum2


def test_ingestion_manager_metadata(tmp_path):
    """Verifies IngestionManager creates complete metadata audit record."""
    test_csv = tmp_path / "test_encounters.csv"
    df = pd.DataFrame({
        "encounter_id": [1, 2, 3],
        "patient_nbr": [10, 20, 30],
        "readmitted": ["NO", "<30", ">30"],
    })
    df.to_csv(test_csv, index=False)

    mgr = IngestionManager(raw_path=test_csv, run_id="TEST_RUN_001")
    meta = mgr.verify_and_audit_raw()

    assert meta["status"] == "SUCCESS"
    assert meta["row_count"] == 3
    assert meta["column_count"] == 3
    assert len(meta["file_checksum"]) == 64
    assert meta["pipeline_run_id"] == "TEST_RUN_001"


def test_missing_file_raises_error(tmp_path):
    """Verifies FileNotFoundError is raised when raw file is missing."""
    non_existent = tmp_path / "non_existent.csv"
    mgr = IngestionManager(raw_path=non_existent)
    with pytest.raises(FileNotFoundError):
        mgr.verify_and_audit_raw()
