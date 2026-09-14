# Academic Course Project Report Outline

**Course:** Data Engineering and MLOps  
**Project Title:** Hospital Readmission Analytics and Prediction Using Public Data (Part 1)  
**Author:** [Student Name / Team Name]  
**Date:** [Date / Semester]  

---

## Abstract
Brief 200–250 word summary covering the clinical background of hospital readmissions, the data engineering challenges of healthcare data, the implementation of the ETL pipeline and PostgreSQL analytical data mart, and key observational findings from the interactive Streamlit dashboard.

---

## 1. Introduction
- Background on hospital readmissions in diabetic patient populations.
- The 30-day readmission metric under the Hospital Readmissions Reduction Program (HRRP).
- Role of reproducible data engineering in healthcare analytics.

---

## 2. Problem Statement
- Healthcare data is heterogeneous, noisy, and subject to strict privacy regulations.
- The challenge of translating raw hospital encounter logs into standardized, privacy-safe, analytical data marts suitable for observational analytics and future predictive modeling.

---

## 3. Objectives
1. Build an automated, reproducible data ingestion and staging pipeline for the UCI 130-US Hospitals dataset.
2. Formulate a comprehensive data quality and validation framework with quarantined error tracking.
3. Design a HIPAA-aligned de-identification layer using cryptographically salted SHA-256 surrogate keys.
4. Deploy a normalized relational database schema and analytical data marts in PostgreSQL.
5. Create an interactive Streamlit dashboard providing executive KPIs, length of stay dynamics, diagnosis breakdowns, and observational cohort rankings.
6. Establish clean modular boundaries for the Part 2 MLOps extension.

---

## 4. Dataset Description
- **Source:** UCI Machine Learning Repository (Dataset #296; Strack et al., 2014).
- **Timeframe & Volume:** 1999–2008 across 130 US hospitals; 101,766 encounters across 71,518 distinct patients.
- **Attributes:** 50 raw features covering demographics, clinical encounters, ICD-9 diagnoses, lab tests, and 23 diabetic medications.
- **Readmission Target:** Standardized classification into `<30` (readmission within 30 days), `>30` (readmission after 30 days), and `NO` (no readmission observed).

---

## 5. Privacy and Ethical Considerations
- Implementation of the HIPAA Safe Harbor standard.
- Explanation of the salted surrogate hashing algorithm:
  $$\text{patient\_key} = \text{SHA-256}(\text{patient\_nbr} + \text{salt})$$
- Verification that raw `patient_nbr` and direct identifiers are purged prior to analytical presentation.
- Ethical boundary: Distinguishing observational cohort patterns from clinical causation.

---

## 6. System Architecture
- Multi-tier Data Lakehouse diagram (Raw Landing, Staging, Validation, Curated, Analytics, UI).
- Airflow orchestration vs. standalone CLI execution.
- Insert Architecture Diagram here:
  > *[Insert diagrams/architecture.mmd rendered image here]*

---

## 7. ETL Pipeline
- Detailed walkthrough of the 12 logical tasks:
  1. `check_source`
  2. `ingest_raw_data`
  3. `validate_schema`
  4. `load_staging`
  5. `clean_data`
  6. `validate_cleaned_data`
  7. `generate_rejected_records`
  8. `engineer_features`
  9. `create_analytical_tables`
  10. `load_postgresql`
  11. `run_quality_checks`
  12. `generate_pipeline_summary`
- Insert Airflow DAG screenshot here:
  > *[Insert Airflow DAG Graph View screenshot here]*

---

## 8. Data Cleaning & Standardization
- Deterministic handling of special missing value tokens (`?`, `Unknown/Invalid`, `Not Mapped`, `NULL`).
- Normalization of lookup codes using `IDs_mapping.csv`.
- Standardization of ICD-9 diagnosis codes into broad clinical categories (Circulatory, Respiratory, Digestive, Diabetes, etc.).

---

## 9. Data Quality Framework
- Formal validation matrix: schema completeness, primary key nullity, duplicate encounter rejection, and numeric bounds ($LOS \ge 0$).
- Quarantining mechanics of `rejected.encounters`.
- Summary of data quality audit results:
  > *[Insert Table or Terminal Output of Data Quality Checks here]*

---

## 10. PostgreSQL Data Model
- Relational schema structure (`staging`, `curated`, `analytics`, `rejected`, `metadata`).
- Normalization into `curated.encounters`, `curated.diagnoses`, `curated.admissions`, and `curated.readmissions`.
- Analytical data marts (`analytics.patient_summary`, `analytics.readmission_summary`, etc.).
- B-Tree indexing strategy for sub-second analytical queries.
  > *[Insert PostgreSQL DDL / Table Count Query screenshot here]*

---

## 11. Feature Engineering
- Clinical feature derivations:
  - `length_of_stay = time_in_hospital`
  - `prior_inpatient_visits`, `prior_emergency_visits`, `prior_outpatient_visits`
  - `medication_count = num_medications`
  - `diagnosis_count = number_diagnoses`
  - `age_group` categorization (`<30`, `30-50`, `50-70`, `70+`)
- Aggregated multi-encounter patient summary features.

---

## 12. Dashboard Design & Interactive Analytics
- Design rationale of the Streamlit application.
- Top-level KPI banner.
- Detailed discussion of the 5 core analytical views:
  1. Readmission by Age Group
  2. Readmission by Diagnosis Category
  3. Length of Stay Distribution & Correlation
  4. Admission Patterns & Discharge Dispositions
  5. Multi-dimensional Cohort Analysis
- Observed High-Readmission Cohorts view and sample threshold controls.
  > *[Insert Streamlit Dashboard Screenshots here]*

---

## 13. Results and Findings
- **Encounter Volume & Patient Count:** Empirical statistics from the actual dataset run (101,766 encounters, 71,518 unique patients).
- **Baseline 30-Day Readmission Rate:** ~11.16%.
- **Length of Stay Dynamics:** Average LOS of 4.4 days; relationship between longer inpatient stays and readmission frequency.
- **Diagnosis Insights:** Highest observed readmission rates observed in Circulatory, Respiratory, and Diabetes primary diagnostic categories.

---

## 14. Limitations
- Retrospective observational data from 1999–2008.
- Absence of clinical lab value details (e.g. continuous blood glucose measurements).
- Unmeasured confounders (social determinants of health, post-discharge medication adherence).

---

## 15. Future MLOps Extension (Part 2 Roadmap)
- Transitioning analytical marts into a Feature Store.
- Candidate ML algorithms (Logistic Regression, Random Forest, XGBoost).
- Experiment tracking with MLflow (parameters, metrics, confusion matrices).
- Model registry and automated fairness evaluation across demographic sub-cohorts.
- FastAPI containerized inference endpoint for real-time risk scoring.

---

## 16. Conclusion
- Summary of Part 1 achievements: a robust, reproducible data platform providing clean data marts and interactive decision support.
- Readiness for Part 2 machine learning predictive model development.

---

## 17. References
1. Strack, B., et al. (2014). "Impact of HbA1c Measurement on Hospital Readmission Rates." *BioMed Research International*.
2. Centers for Medicare & Medicaid Services (CMS). "Hospital Readmissions Reduction Program (HRRP)."
3. UCI Machine Learning Repository: Diabetes 130-US Hospitals (1999-2008).
