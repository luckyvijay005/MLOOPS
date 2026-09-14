-- ============================================================================
-- 02_create_tables.sql
-- Hospital Readmission Analytics Database - Table Definitions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Metadata Layer: Ingestion Tracking & Audit Log
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.etl_ingestion_log (
    ingestion_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_file VARCHAR(255) NOT NULL,
    extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_checksum VARCHAR(64) NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    pipeline_run_id VARCHAR(64) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. Staging Layer: Raw Diabetic Encounters (Preserves original source fields)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.diabetic_encounters (
    encounter_id VARCHAR(50),
    patient_nbr VARCHAR(50),
    race VARCHAR(50),
    gender VARCHAR(50),
    age VARCHAR(50),
    weight VARCHAR(50),
    admission_type_id VARCHAR(50),
    discharge_disposition_id VARCHAR(50),
    admission_source_id VARCHAR(50),
    time_in_hospital VARCHAR(50),
    payer_code VARCHAR(50),
    medical_specialty VARCHAR(100),
    num_lab_procedures VARCHAR(50),
    num_procedures VARCHAR(50),
    num_medications VARCHAR(50),
    number_outpatient VARCHAR(50),
    number_emergency VARCHAR(50),
    number_inpatient VARCHAR(50),
    diag_1 VARCHAR(50),
    diag_2 VARCHAR(50),
    diag_3 VARCHAR(50),
    number_diagnoses VARCHAR(50),
    max_glu_serum VARCHAR(50),
    a1cresult VARCHAR(50),
    metformin VARCHAR(50),
    repaglinide VARCHAR(50),
    nateglinide VARCHAR(50),
    chlorpropamide VARCHAR(50),
    glimepiride VARCHAR(50),
    acetohexamide VARCHAR(50),
    glipizide VARCHAR(50),
    glyburide VARCHAR(50),
    tolbutamide VARCHAR(50),
    pioglitazone VARCHAR(50),
    rosiglitazone VARCHAR(50),
    acarbose VARCHAR(50),
    miglitol VARCHAR(50),
    troglitazone VARCHAR(50),
    tolazamide VARCHAR(50),
    examide VARCHAR(50),
    citagliptin VARCHAR(50),
    insulin VARCHAR(50),
    glyburide_metformin VARCHAR(50),
    glipizide_metformin VARCHAR(50),
    glimepiride_pioglitazone VARCHAR(50),
    metformin_rosiglitazone VARCHAR(50),
    metformin_pioglitazone VARCHAR(50),
    change VARCHAR(50),
    diabetesmed VARCHAR(50),
    readmitted VARCHAR(50),
    pipeline_run_id VARCHAR(64),
    staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Rejected Layer: Failed Quality Checks & Duplicates
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rejected.encounters (
    rejection_id SERIAL PRIMARY KEY,
    original_encounter_id VARCHAR(100),
    rejection_reason VARCHAR(255) NOT NULL,
    rejected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id VARCHAR(64) NOT NULL,
    source_file VARCHAR(255),
    raw_record_snippet TEXT
);

-- ----------------------------------------------------------------------------
-- 4. Curated Layer: Privacy-Protected, Standardized Relational Entities
-- ----------------------------------------------------------------------------

-- Main Curated Encounters
CREATE TABLE IF NOT EXISTS curated.encounters (
    encounter_key VARCHAR(64) PRIMARY KEY,
    patient_key VARCHAR(64) NOT NULL,
    encounter_id_surrogate VARCHAR(64) NOT NULL,
    age_group VARCHAR(20) NOT NULL,
    gender VARCHAR(20),
    race VARCHAR(50),
    admission_type VARCHAR(100) NOT NULL,
    discharge_disposition VARCHAR(100) NOT NULL,
    admission_source VARCHAR(100) NOT NULL,
    time_in_hospital INTEGER NOT NULL,
    num_lab_procedures INTEGER NOT NULL,
    num_procedures INTEGER NOT NULL,
    num_medications INTEGER NOT NULL,
    number_outpatient INTEGER NOT NULL,
    number_emergency INTEGER NOT NULL,
    number_inpatient INTEGER NOT NULL,
    number_diagnoses INTEGER NOT NULL,
    readmission_status VARCHAR(20) NOT NULL,
    readmitted_30d INTEGER NOT NULL,
    pipeline_run_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Normalized Diagnoses Table
CREATE TABLE IF NOT EXISTS curated.diagnoses (
    diagnosis_key VARCHAR(64) PRIMARY KEY,
    encounter_key VARCHAR(64) NOT NULL REFERENCES curated.encounters(encounter_key) ON DELETE CASCADE,
    diagnosis_position INTEGER NOT NULL,
    diagnosis_code VARCHAR(20),
    diagnosis_category VARCHAR(100) NOT NULL
);

-- Normalized Admissions Table
CREATE TABLE IF NOT EXISTS curated.admissions (
    admission_key VARCHAR(64) PRIMARY KEY,
    encounter_key VARCHAR(64) NOT NULL REFERENCES curated.encounters(encounter_key) ON DELETE CASCADE,
    patient_key VARCHAR(64) NOT NULL,
    admission_type VARCHAR(100) NOT NULL,
    admission_source VARCHAR(100) NOT NULL,
    discharge_disposition VARCHAR(100) NOT NULL,
    admission_sequence INTEGER DEFAULT 1,
    length_of_stay INTEGER NOT NULL,
    prior_outpatient_visits INTEGER NOT NULL,
    prior_emergency_visits INTEGER NOT NULL,
    prior_inpatient_visits INTEGER NOT NULL
);

-- Normalized Readmissions Table
CREATE TABLE IF NOT EXISTS curated.readmissions (
    readmission_key VARCHAR(64) PRIMARY KEY,
    encounter_key VARCHAR(64) NOT NULL REFERENCES curated.encounters(encounter_key) ON DELETE CASCADE,
    patient_key VARCHAR(64) NOT NULL,
    readmission_status VARCHAR(20) NOT NULL,
    readmitted_30d INTEGER NOT NULL,
    readmission_category VARCHAR(50) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 5. Analytics Layer: Data Marts & Pre-Aggregated Summary Tables
-- ----------------------------------------------------------------------------

-- Patient Analytical Summary (1 row per surrogate patient_key)
CREATE TABLE IF NOT EXISTS analytics.patient_summary (
    patient_key VARCHAR(64) PRIMARY KEY,
    total_encounters INTEGER NOT NULL,
    total_inpatient_visits INTEGER NOT NULL,
    total_emergency_visits INTEGER NOT NULL,
    total_outpatient_visits INTEGER NOT NULL,
    average_length_of_stay NUMERIC(6, 2) NOT NULL,
    average_medications NUMERIC(6, 2) NOT NULL,
    average_diagnoses NUMERIC(6, 2) NOT NULL,
    number_of_readmissions INTEGER NOT NULL,
    readmission_rate NUMERIC(6, 4) NOT NULL,
    first_encounter_los INTEGER,
    last_encounter_los INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Readmission Summary Data Mart
CREATE TABLE IF NOT EXISTS analytics.readmission_summary (
    summary_id SERIAL PRIMARY KEY,
    age_group VARCHAR(20) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    race VARCHAR(50),
    admission_type VARCHAR(100) NOT NULL,
    total_encounters INTEGER NOT NULL,
    readmitted_30d_count INTEGER NOT NULL,
    readmission_rate_30d NUMERIC(6, 4) NOT NULL,
    readmission_over30d_count INTEGER NOT NULL,
    no_readmission_count INTEGER NOT NULL,
    avg_length_of_stay NUMERIC(6, 2) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Admission Pattern Summary Data Mart
CREATE TABLE IF NOT EXISTS analytics.admission_summary (
    summary_id SERIAL PRIMARY KEY,
    admission_type VARCHAR(100) NOT NULL,
    admission_source VARCHAR(100) NOT NULL,
    discharge_disposition VARCHAR(100) NOT NULL,
    total_encounters INTEGER NOT NULL,
    readmitted_30d_count INTEGER NOT NULL,
    readmission_rate_30d NUMERIC(6, 4) NOT NULL,
    avg_length_of_stay NUMERIC(6, 2) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Diagnosis Category Summary Data Mart
CREATE TABLE IF NOT EXISTS analytics.diagnosis_summary (
    summary_id SERIAL PRIMARY KEY,
    diagnosis_category VARCHAR(100) NOT NULL,
    diagnosis_position INTEGER NOT NULL,
    total_diagnoses INTEGER NOT NULL,
    readmitted_30d_count INTEGER NOT NULL,
    readmission_rate_30d NUMERIC(6, 4) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Length of Stay Summary Data Mart
CREATE TABLE IF NOT EXISTS analytics.length_of_stay_summary (
    summary_id SERIAL PRIMARY KEY,
    length_of_stay INTEGER NOT NULL,
    total_encounters INTEGER NOT NULL,
    readmitted_30d_count INTEGER NOT NULL,
    readmission_rate_30d NUMERIC(6, 4) NOT NULL,
    avg_medications NUMERIC(6, 2) NOT NULL,
    avg_diagnoses NUMERIC(6, 2) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
