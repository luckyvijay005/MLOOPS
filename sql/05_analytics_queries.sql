-- ============================================================================
-- 05_analytics_queries.sql
-- Hospital Readmission Analytics Database - Standard Analytical Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. High-Level Population KPIs: Encounters, Patients, & Readmission Rates
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_encounters,
    COUNT(DISTINCT patient_key) AS unique_patients,
    SUM(CASE WHEN readmitted_30d = 1 THEN 1 ELSE 0 END) AS count_readmitted_30d,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct,
    SUM(CASE WHEN readmission_status = '>30' THEN 1 ELSE 0 END) AS count_readmitted_over_30d,
    ROUND((SUM(CASE WHEN readmission_status = '>30' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS readmission_rate_over_30d_pct,
    SUM(CASE WHEN readmission_status = 'NO' THEN 1 ELSE 0 END) AS count_no_readmission,
    ROUND((SUM(CASE WHEN readmission_status = 'NO' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS no_readmission_rate_pct
FROM curated.encounters;

-- ----------------------------------------------------------------------------
-- 2. Readmission Breakdown by Age Group
-- ----------------------------------------------------------------------------
SELECT 
    age_group,
    COUNT(*) AS total_encounters,
    SUM(readmitted_30d) AS readmitted_30d_count,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct,
    ROUND(AVG(time_in_hospital)::NUMERIC, 2) AS avg_length_of_stay,
    ROUND(AVG(num_medications)::NUMERIC, 2) AS avg_medications
FROM curated.encounters
GROUP BY age_group
ORDER BY age_group;

-- ----------------------------------------------------------------------------
-- 3. Readmission Breakdown by Primary Diagnosis Category
-- ----------------------------------------------------------------------------
SELECT 
    d.diagnosis_category,
    COUNT(DISTINCT e.encounter_key) AS total_encounters,
    SUM(e.readmitted_30d) AS readmissions_30d,
    ROUND(AVG(e.readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct,
    ROUND(AVG(e.time_in_hospital)::NUMERIC, 2) AS avg_length_of_stay
FROM curated.diagnoses d
JOIN curated.encounters e ON d.encounter_key = e.encounter_key
WHERE d.diagnosis_position = 1
GROUP BY d.diagnosis_category
ORDER BY readmission_rate_30d_pct DESC;

-- ----------------------------------------------------------------------------
-- 4. Length of Stay Distribution and Correlation with Readmission
-- ----------------------------------------------------------------------------
SELECT 
    time_in_hospital AS length_of_stay_days,
    COUNT(*) AS encounter_count,
    SUM(readmitted_30d) AS readmitted_30d_count,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_pct,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY num_medications) AS median_medications
FROM curated.encounters
GROUP BY time_in_hospital
ORDER BY length_of_stay_days;

-- ----------------------------------------------------------------------------
-- 5. Admission Patterns: Admission Type vs Discharge Disposition
-- ----------------------------------------------------------------------------
SELECT 
    a.admission_type,
    a.discharge_disposition,
    COUNT(*) AS total_admissions,
    SUM(e.readmitted_30d) AS readmissions_30d,
    ROUND(AVG(e.readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_pct
FROM curated.admissions a
JOIN curated.encounters e ON a.encounter_key = e.encounter_key
GROUP BY a.admission_type, a.discharge_disposition
HAVING COUNT(*) >= 50
ORDER BY total_admissions DESC;

-- ----------------------------------------------------------------------------
-- 6. Admission Volume by Admission Source
-- ----------------------------------------------------------------------------
SELECT 
    admission_source,
    COUNT(*) AS total_encounters,
    ROUND((COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100, 2) AS pct_of_total_volume,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct
FROM curated.encounters
GROUP BY admission_source
ORDER BY total_encounters DESC;

-- ----------------------------------------------------------------------------
-- 7. Observed High-Readmission Cohorts (Minimum 100 encounters threshold)
-- Note: Historical association does not imply clinical risk or causation.
-- ----------------------------------------------------------------------------
SELECT 
    age_group,
    gender,
    admission_type,
    COUNT(*) AS cohort_size,
    SUM(readmitted_30d) AS readmission_30d_count,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_pct,
    ROUND(AVG(time_in_hospital)::NUMERIC, 2) AS avg_los
FROM curated.encounters
GROUP BY age_group, gender, admission_type
HAVING COUNT(*) >= 100
ORDER BY readmission_rate_pct DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- 8. Medication Count Analysis vs Readmission
-- ----------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN num_medications BETWEEN 1 AND 5 THEN '1-5 (Low)'
        WHEN num_medications BETWEEN 6 AND 15 THEN '6-15 (Moderate)'
        WHEN num_medications BETWEEN 16 AND 25 THEN '16-25 (High)'
        ELSE '26+ (Very High)'
    END AS medication_tier,
    COUNT(*) AS total_encounters,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct,
    ROUND(AVG(time_in_hospital)::NUMERIC, 2) AS avg_length_of_stay
FROM curated.encounters
GROUP BY 1
ORDER BY MIN(num_medications);

-- ----------------------------------------------------------------------------
-- 9. Diagnosis Count Analysis vs Readmission
-- ----------------------------------------------------------------------------
SELECT 
    number_diagnoses,
    COUNT(*) AS total_encounters,
    SUM(readmitted_30d) AS readmission_30d_count,
    ROUND(AVG(readmitted_30d)::NUMERIC * 100, 2) AS readmission_rate_30d_pct,
    ROUND(AVG(num_medications)::NUMERIC, 2) AS avg_medications
FROM curated.encounters
GROUP BY number_diagnoses
ORDER BY number_diagnoses;

-- ----------------------------------------------------------------------------
-- 10. Patient Multi-Encounter Summary (Frequent Inpatient Cohort Analysis)
-- ----------------------------------------------------------------------------
SELECT 
    total_encounters,
    COUNT(patient_key) AS patient_count,
    ROUND(AVG(readmission_rate)::NUMERIC * 100, 2) AS avg_patient_readmission_rate_pct,
    ROUND(AVG(average_length_of_stay)::NUMERIC, 2) AS avg_patient_los
FROM analytics.patient_summary
GROUP BY total_encounters
ORDER BY total_encounters;
