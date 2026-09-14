# Hospital Readmission Analytics - Data Quality & Validation Rules

This document specifies the data quality (DQ) validation framework applied during data transformation. Records failing Critical severity checks are isolated in `rejected.encounters` and logged with explicit rejection reasons.

---

## 1. Validation Rule Matrix

| Rule ID | Field / Table | Validation Type | Expected Condition | Severity | Action if Failed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DQ001** | `diabetic_data.csv` | File Integrity & Schema | Input file exists and contains all 17 required columns | **Critical** | Fail ingestion stage, log error to `metadata.etl_ingestion_log` |
| **DQ002** | `encounter_id` | Nullity Check | Non-null, non-empty string | **Critical** | Reject record with reason `MISSING_ENCOUNTER_ID` |
| **DQ003** | `patient_nbr` | Nullity Check | Non-null, non-empty string | **Critical** | Reject record with reason `MISSING_PATIENT_NBR` |
| **DQ004** | `encounter_id` | Uniqueness | No duplicated encounter identifiers in dataset | **Critical** | Reject subsequent duplicates with `DUPLICATE_ENCOUNTER_ID` |
| **DQ005** | `time_in_hospital` | Numeric Bounds | Integer value $\ge 0$ (expected 1–14 days) | **Critical** | Reject record with `INVALID_TIME_IN_HOSPITAL_BOUNDS` |
| **DQ006** | `num_lab_procedures` | Numeric Bounds | Integer value $\ge 0$ | **Critical** | Reject record with `INVALID_NUM_LAB_PROCEDURES_BOUNDS` |
| **DQ007** | `num_procedures` | Numeric Bounds | Integer value $\ge 0$ and $\le 6$ | **Critical** | Reject record with `INVALID_NUM_PROCEDURES_BOUNDS` |
| **DQ008** | `num_medications` | Numeric Bounds | Integer value $\ge 0$ | **Critical** | Reject record with `INVALID_NUM_MEDICATIONS_BOUNDS` |
| **DQ009** | `number_outpatient` | Numeric Bounds | Integer value $\ge 0$ | **Critical** | Reject record with `INVALID_NUMBER_OUTPATIENT_BOUNDS` |
| **DQ010** | `number_emergency` | Numeric Bounds | Integer value $\ge 0$ | **Critical** | Reject record with `INVALID_NUMBER_EMERGENCY_BOUNDS` |
| **DQ011** | `number_inpatient` | Numeric Bounds | Integer value $\ge 0$ | **Critical** | Reject record with `INVALID_NUMBER_INPATIENT_BOUNDS` |
| **DQ012** | `number_diagnoses` | Numeric Bounds | Integer value $\ge 0$ and $\le 16$ | **Critical** | Reject record with `INVALID_NUMBER_DIAGNOSES_BOUNDS` |
| **DQ013** | `age` | Categorical Domain | Value in allowed brackets: `[0-10)`, ..., `[90-100)` | **Warning** | Map unknown brackets to `Unknown` |
| **DQ014** | `gender` | Categorical Domain | Value in `{Female, Male, Unknown/Invalid}` | **Warning** | Preserve reported value; clean whitespace |
| **DQ015** | `readmitted` | Target Normalization | Valid code in `{'<30', '>30', 'NO'}` | **Warning** | If missing or anomalous, map to `NO` |
| **DQ016** | `race` | Missing Value Code | Strings `?`, `None`, `NULL` | **Informational** | Normalize to explicit `NULL` / `Other` |
| **DQ017** | `diag_1, diag_2, diag_3` | Clinical Mapping | ICD-9 code maps to recognized clinical category | **Informational** | Assign `Other` or `Missing/Unknown` |
| **DQ018** | `curated.encounters` | Primary Key Integrity | `encounter_key` is unique across curated table | **Critical** | Abort relational load; roll back transaction |

---

## 2. Rejection Handling Architecture
When an encounter violates a **Critical** validation rule:
1. It is excluded from `curated.encounters`, `curated.diagnoses`, `curated.admissions`, and `curated.readmissions`.
2. An audit entry is created in `rejected.encounters` capturing:
   - `rejection_id`: Unique tracking ID (`REJ_<run_id>_<sequence>`)
   - `original_encounter_id`: Source identifier for traceability
   - `rejection_reason`: Explicit rule violation tag (e.g., `DUPLICATE_ENCOUNTER_ID`)
   - `rejected_at`: UTC timestamp of validation run
   - `pipeline_run_id`: Associated execution run ID
   - `source_file`: Ingested file name
   - `raw_record_snippet`: JSON snippet of the invalid raw record
3. Summary rejection counts are aggregated and recorded in the run summary report.
