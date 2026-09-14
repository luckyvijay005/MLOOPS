# Hospital Readmission Analytics - Data Dictionary

This data dictionary documents attributes across the Raw, Staging, Curated, and Analytics layers of the Hospital Readmission Analytics platform.

---

## 1. Patient Privacy & De-Identification Policy
- **Healthcare Privacy Standard:** Complies with HIPAA Safe Harbor de-identification rules.
- **Surrogate Shielding:** Raw patient identifiers (`patient_nbr`) and encounter IDs (`encounter_id`) are transformed into cryptographically salted SHA-256 surrogate keys:
  $$\text{patient\_key} = \text{SHA-256}(\text{patient\_nbr} + \text{PROJECT\_PATIENT\_SALT})$$
- **Zero Identifier Leakage:** Raw `patient_nbr` is completely dropped during feature engineering and never persisted into curated or analytical data marts.
- **Privacy Classification Levels:**
  - `IDENTIFIER_DROPPED`: Source identifier removed during ingestion/transformation.
  - `SURROGATE_KEY`: Deterministic pseudonymized hash used for relational linking.
  - `DE-IDENTIFIED_CLINICAL`: De-identified clinical or encounter attribute.
  - `DERIVED_AGGREGATE`: Pre-aggregated statistical metric.

---

## 2. Comprehensive Field Dictionary

| Field | Description | Type | Source | Transformation | Privacy Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **encounter_id** | Unique identifier for inpatient encounter | VARCHAR | Raw CSV | Stored in staging; replaced by surrogate in curated layer | `IDENTIFIER_DROPPED` |
| **patient_nbr** | Source patient tracking number | VARCHAR | Raw CSV | Stored in staging; hashed with salt and purged | `IDENTIFIER_DROPPED` |
| **encounter_key** | Cryptographic encounter surrogate key | VARCHAR(64) | Pipeline | SHA-256(encounter_id + salt) | `SURROGATE_KEY` |
| **encounter_id_surrogate** | Truncated display-safe encounter token | VARCHAR(16) | Pipeline | encounter_key[:16] | `SURROGATE_KEY` |
| **patient_key** | Cryptographic patient surrogate key | VARCHAR(64) | Pipeline | SHA-256(patient_nbr + salt) | `SURROGATE_KEY` |
| **age** | Original 10-year age bracket (e.g. `[50-60)`) | VARCHAR(20) | Raw CSV | Whitespace stripped, missing mapped to NULL | `DE-IDENTIFIED_CLINICAL` |
| **age_group** | Standardized clinical age category (`<30`, `30-50`, `50-70`, `70+`) | VARCHAR(20) | Derived | Mapped from 10-year age brackets | `DE-IDENTIFIED_CLINICAL` |
| **gender** | Patient gender (`Female`, `Male`, `Unknown/Invalid`) | VARCHAR(20) | Raw CSV | Whitespace stripped, standardized | `DE-IDENTIFIED_CLINICAL` |
| **race** | Reported race/ethnicity (`Caucasian`, `AfricanAmerican`, etc.) | VARCHAR(50) | Raw CSV | `?` replaced with NULL / `Other` | `DE-IDENTIFIED_CLINICAL` |
| **admission_type_id** | Numeric code for encounter admission type | INTEGER | Raw CSV | Converted to integer lookup code | `DE-IDENTIFIED_CLINICAL` |
| **admission_type** | Descriptive admission type (`Emergency`, `Urgent`, `Elective`, etc.) | VARCHAR(100) | Derived | Looked up via `IDs_mapping.csv` | `DE-IDENTIFIED_CLINICAL` |
| **discharge_disposition_id** | Numeric code for discharge status | INTEGER | Raw CSV | Converted to integer lookup code | `DE-IDENTIFIED_CLINICAL` |
| **discharge_disposition** | Descriptive discharge disposition (`Discharged to home`, `SNF`, etc.) | VARCHAR(100) | Derived | Looked up via `IDs_mapping.csv` | `DE-IDENTIFIED_CLINICAL` |
| **admission_source_id** | Numeric code for referral intake route | INTEGER | Raw CSV | Converted to integer lookup code | `DE-IDENTIFIED_CLINICAL` |
| **admission_source** | Descriptive admission source (`Physician Referral`, `Emergency Room`, etc.) | VARCHAR(100) | Derived | Looked up via `IDs_mapping.csv` | `DE-IDENTIFIED_CLINICAL` |
| **time_in_hospital** | Duration of hospital stay in days (range 1–14) | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **length_of_stay** | Synonymous with time_in_hospital (days) | INTEGER | Derived | Direct assignment from `time_in_hospital` | `DE-IDENTIFIED_CLINICAL` |
| **num_lab_procedures** | Count of lab tests performed during encounter | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **num_procedures** | Count of non-lab medical procedures performed | INTEGER | Raw CSV | Validated non-negative integer (0–6) | `DE-IDENTIFIED_CLINICAL` |
| **num_medications** | Count of distinct medications administered | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **medication_count** | Total medication administrations | INTEGER | Derived | Direct assignment from `num_medications` | `DE-IDENTIFIED_CLINICAL` |
| **number_outpatient** | Outpatient visits in year prior to encounter | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **prior_outpatient_visits** | Historical outpatient utilization feature | INTEGER | Derived | Cast to integer feature | `DE-IDENTIFIED_CLINICAL` |
| **number_emergency** | Emergency room visits in year prior to encounter | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **prior_emergency_visits** | Historical emergency room utilization feature | INTEGER | Derived | Cast to integer feature | `DE-IDENTIFIED_CLINICAL` |
| **number_inpatient** | Inpatient admissions in year prior to encounter | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **prior_inpatient_visits** | Historical inpatient utilization feature | INTEGER | Derived | Cast to integer feature | `DE-IDENTIFIED_CLINICAL` |
| **number_diagnoses** | Number of diagnoses entered into hospital billing system | INTEGER | Raw CSV | Validated non-negative integer | `DE-IDENTIFIED_CLINICAL` |
| **diagnosis_count** | Total recorded diagnoses | INTEGER | Derived | Cast to integer feature | `DE-IDENTIFIED_CLINICAL` |
| **diag_1** | Primary ICD-9 diagnosis billing code | VARCHAR(20) | Raw CSV | Missing codes mapped to NULL | `DE-IDENTIFIED_CLINICAL` |
| **diag_2** | Secondary ICD-9 diagnosis billing code | VARCHAR(20) | Raw CSV | Missing codes mapped to NULL | `DE-IDENTIFIED_CLINICAL` |
| **diag_3** | Tertiary ICD-9 diagnosis billing code | VARCHAR(20) | Raw CSV | Missing codes mapped to NULL | `DE-IDENTIFIED_CLINICAL` |
| **diagnosis_key** | Surrogate key for diagnosis record | VARCHAR(64) | Pipeline | SHA-256(encounter_key + position) | `SURROGATE_KEY` |
| **diagnosis_position** | Ordinal position of diagnosis (1=Primary, 2=Secondary, 3=Tertiary) | INTEGER | Derived | Unpivoted diagnosis position index | `DE-IDENTIFIED_CLINICAL` |
| **diagnosis_category** | Broad clinical grouping (`Circulatory`, `Respiratory`, `Diabetes`, etc.) | VARCHAR(100) | Derived | ICD-9 numerical range taxonomy | `DE-IDENTIFIED_CLINICAL` |
| **readmitted** | Original dataset readmission code (`<30`, `>30`, `NO`) | VARCHAR(10) | Raw CSV | Trimmed, validated against allowed set | `DE-IDENTIFIED_CLINICAL` |
| **readmission_status** | Standardized readmission status (`<30`, `>30`, `NO`) | VARCHAR(10) | Derived | Normalized string | `DE-IDENTIFIED_CLINICAL` |
| **readmitted_30d** | Binary 30-day readmission outcome (1 if `<30`, else 0) | INTEGER | Derived | 1 for readmission within 30 days, 0 otherwise | `DE-IDENTIFIED_CLINICAL` |
| **total_encounters** | Total encounters for patient / cohort | INTEGER | Analytics | Pre-aggregated COUNT() | `DERIVED_AGGREGATE` |
| **readmission_rate_30d** | Proportion of encounters readmitted within 30 days | NUMERIC | Analytics | Pre-aggregated AVG(readmitted_30d) | `DERIVED_AGGREGATE` |
| **rejection_reason** | Explanatory error tag for rejected encounter | VARCHAR(255) | Pipeline | Set by quality validation rule | `PIPELINE_METADATA` |
| **pipeline_run_id** | Unique pipeline execution tracking token | VARCHAR(64) | Pipeline | Set by orchestrator per execution | `PIPELINE_METADATA` |
