# Pipeline Execution Evidence & Academic Verification Guide

This document records reproduction steps and contains placeholders for capturing required screenshots demonstrating successful pipeline execution for course grading.

---

## 1. Dataset Download Verification
**Command Executed:**
```bash
python src/ingestion/download_dataset.py
```
**Terminal Output Evidence:**
```text
2026-09-11 22:35:19 | INFO | hospital_pipeline | Attempting to download dataset from: https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip
2026-09-11 22:35:22 | INFO | hospital_pipeline | Archive downloaded successfully. Extracting contents...
2026-09-11 22:35:22 | INFO | hospital_pipeline | Extracted diabetic_data.csv to C:\Users\User\Desktop\ML OPS\data\raw\diabetic_data.csv
2026-09-11 22:35:22 | INFO | hospital_pipeline | Dataset download and extraction complete.
```
> **[Screenshot Placeholder 1]:** *Capture the `data/raw/` directory showing `diabetic_data.csv` (19.1 MB) and `IDs_mapping.csv`.*

---

## 2. Raw File Audit & Cryptographic Checksum
**Command Executed:**
```bash
python -c "from src.ingestion.ingest import IngestionManager; mgr = IngestionManager(); print(mgr.verify_and_audit_raw())"
```
**Verification Evidence:**
- **Source File:** `diabetic_data.csv`
- **Row Count:** `101,766`
- **Column Count:** `50`
- **File Size:** `19,159,383 bytes`
- **SHA-256 Checksum:** `0689e7ec03126dd183ef99516ca4d081f96440db7f9aa0a69a23c316773a985d`
- **Status:** `SUCCESS`

> **[Screenshot Placeholder 2]:** *Capture terminal output showing raw file checksum and row count verification.*

---

## 3. Airflow DAG Definition & Syntax Validation
**DAG Name:** `hospital_readmission_etl`  
**File:** `airflow/dags/hospital_readmission_etl.py`

**Validation Command:**
```bash
python airflow/dags/hospital_readmission_etl.py
```
*(Exits with 0 error code; confirms error-free syntax and modular task definitions).*

> **[Screenshot Placeholder 3]:** *Capture Apache Airflow Webserver UI / Graph View showing the 12 tasks (`check_source` -> `generate_pipeline_summary`).*

---

## 4. End-to-End Pipeline Execution
**Command Executed:**
```bash
python scripts/run_pipeline.py
```
**Execution Summary Output:**
```text
================================================================================
STARTING HOSPITAL READMISSION PIPELINE: RUN_20260911_170533
================================================================================
Raw file verified: 101766 rows, 50 columns, size: 19159383 bytes, SHA-256: 0689e7ec0312...
Successfully staged 101766 rows to data/staging/staging_diabetic_encounters_...
Starting data cleaning on 101766 records...
Data cleaning completed successfully.
Schema validation passed. Found all 17 required columns.
Validation complete: 101766 valid records, 0 rejected records.
Engineering features and privacy surrogate keys...
Relational entities built: 101766 encounters, 303496 diagnoses, 101766 admissions, 101766 readmissions.
Patient summary created for 71518 unique patients.
Building analytical data marts...
================================================================================
PIPELINE COMPLETED SUCCESSFULLY in 19.87s
Curated Encounters: 101766 | Rejected: 0
================================================================================
```
> **[Screenshot Placeholder 4]:** *Capture terminal output of the completed pipeline execution displaying row counts and completion time.*

---

## 5. Automated Pytest Test Suite
**Command Executed:**
```bash
python -m pytest tests/ -v
```
**Test Results Evidence:**
```text
============================= test session starts =============================
collected 18 items

tests/test_database.py::test_sql_ddl_files_exist PASSED                  [  5%]
tests/test_database.py::test_database_manager_offline_handling PASSED    [ 11%]
tests/test_database.py::test_analytics_mart_builder PASSED               [ 16%]
tests/test_ingestion.py::test_synthetic_data_generation PASSED           [ 22%]
tests/test_ingestion.py::test_sha256_checksum PASSED                     [ 27%]
tests/test_ingestion.py::test_ingestion_manager_metadata PASSED          [ 33%]
tests/test_ingestion.py::test_missing_file_raises_error PASSED           [ 38%]
tests/test_transformations.py::test_missing_value_cleaning PASSED        [ 44%]
tests/test_transformations.py::test_readmission_normalization PASSED     [ 50%]
tests/test_transformations.py::test_age_group_mapping PASSED             [ 55%]
tests/test_transformations.py::test_icd9_categorization PASSED           [ 61%]
tests/test_transformations.py::test_surrogate_key_properties PASSED      [ 66%]
tests/test_transformations.py::test_feature_engineering_pipeline PASSED  [ 72%]
tests/test_validation.py::test_schema_validation_success PASSED          [ 77%]
tests/test_validation.py::test_schema_validation_failure PASSED          [ 83%]
tests/test_validation.py::test_duplicate_encounter_rejection PASSED      [ 88%]
tests/test_validation.py::test_null_encounter_id_rejection PASSED        [ 94%]
tests/test_validation.py::test_negative_numeric_bound_rejection PASSED   [100%]

============================= 18 passed in 8.68s ==============================
```
> **[Screenshot Placeholder 5]:** *Capture terminal output showing all 18 passing unit and integration tests.*

---

## 6. PostgreSQL Relational Schema & Table Counts
**Command Executed in psql / pgAdmin / Docker:**
```sql
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema IN ('staging', 'curated', 'analytics', 'rejected', 'metadata');
```
> **[Screenshot Placeholder 6]:** *Capture pgAdmin or terminal output displaying tables in `staging`, `curated`, `analytics`, `rejected`, and `metadata`.*

---

## 7. Streamlit Interactive Dashboard
**Command Executed:**
```bash
python scripts/run_dashboard.py
```
> **[Screenshot Placeholder 7A]:** *Capture the Streamlit Dashboard KPI Overview Banner (Total Encounters: 101,766 | Unique Patients: 71,518 | 30-Day Readmission Rate: 11.16%).*  
> **[Screenshot Placeholder 7B]:** *Capture View 1 (Readmission by Age Group chart).*  
> **[Screenshot Placeholder 7C]:** *Capture View 2 (Readmission by Diagnosis Category).*  
> **[Screenshot Placeholder 7D]:** *Capture View 3 (Length of Stay Dynamics).*  
> **[Screenshot Placeholder 7E]:** *Capture View 4 (Hierarchical Admission & Discharge Patterns).*  
> **[Screenshot Placeholder 7F]:** *Capture View 5 (Dynamic Cohort Analysis).*  
> **[Screenshot Placeholder 7G]:** *Capture Observed High-Readmission Cohorts view with sample threshold controls.*

---

## 8. Analytical SQL Query Execution
**Script:** `sql/05_analytics_queries.sql`  
Execute queries in PostgreSQL to demonstrate query performance and consistency with the dashboard metrics.
> **[Screenshot Placeholder 8]:** *Capture SQL query results from Query 1 (Population KPIs) and Query 7 (High Readmission Cohorts).*
