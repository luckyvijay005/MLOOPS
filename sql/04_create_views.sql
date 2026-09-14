-- ============================================================================
-- 04_create_views.sql
-- Hospital Readmission Analytics Database - Analytical Views
-- ============================================================================

-- Overall Executive KPI View
CREATE OR REPLACE VIEW analytics.v_kpi_overview AS
SELECT 
    COUNT(*) AS total_encounters,
    COUNT(DISTINCT patient_key) AS unique_patients,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS readmissions_30d,
    ROUND(AVG(readmitted_30d)::NUMERIC, 4) AS readmission_rate_30d,
    SUM(CASE WHEN readmission_status = '>30' THEN 1 ELSE 0 END) AS readmissions_over30d,
    ROUND((SUM(CASE WHEN readmission_status = '>30' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0))::NUMERIC, 4) AS readmission_rate_over30d,
    SUM(CASE WHEN readmission_status = 'NO' THEN 1 ELSE 0 END) AS no_readmission_count,
    ROUND((SUM(CASE WHEN readmission_status = 'NO' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0))::NUMERIC, 4) AS no_readmission_rate,
    ROUND(AVG(time_in_hospital)::NUMERIC, 2) AS avg_length_of_stay,
    ROUND(AVG(num_medications)::NUMERIC, 2) AS avg_num_medications,
    ROUND(AVG(number_diagnoses)::NUMERIC, 2) AS avg_num_diagnoses
FROM curated.encounters;

-- Observed High-Readmission Cohorts View (Enforces min sample size of 100 encounters)
-- Note: Historical association does not imply clinical risk or causation.
CREATE OR REPLACE VIEW analytics.v_cohort_readmission_ranking AS
SELECT 
    e.age_group,
    e.gender,
    e.admission_type,
    COUNT(*) AS cohort_encounters,
    SUM(e.readmitted_30d) AS cohort_readmissions_30d,
    ROUND((SUM(e.readmitted_30d)::NUMERIC / NULLIF(COUNT(*), 0))::NUMERIC, 4) AS readmission_rate_30d,
    ROUND(AVG(e.time_in_hospital)::NUMERIC, 2) AS avg_length_of_stay,
    ROUND(AVG(e.num_medications)::NUMERIC, 2) AS avg_medications
FROM curated.encounters e
GROUP BY e.age_group, e.gender, e.admission_type
HAVING COUNT(*) >= 100
ORDER BY readmission_rate_30d DESC;

-- Length of Stay vs Readmission Analysis View
CREATE OR REPLACE VIEW analytics.v_los_vs_readmission AS
SELECT 
    time_in_hospital AS length_of_stay,
    COUNT(*) AS total_encounters,
    SUM(readmitted_30d) AS readmissions_30d,
    ROUND((SUM(readmitted_30d)::NUMERIC / NULLIF(COUNT(*), 0))::NUMERIC, 4) AS readmission_rate_30d,
    ROUND(AVG(num_medications)::NUMERIC, 2) AS avg_medications,
    ROUND(AVG(num_lab_procedures)::NUMERIC, 2) AS avg_lab_procedures
FROM curated.encounters
GROUP BY time_in_hospital
ORDER BY time_in_hospital;
