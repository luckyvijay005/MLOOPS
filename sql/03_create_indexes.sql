-- ============================================================================
-- 03_create_indexes.sql
-- Hospital Readmission Analytics Database - Performance Indexes
-- ============================================================================

-- Curated Encounters Indexes
CREATE INDEX IF NOT EXISTS idx_curated_enc_patient_key 
    ON curated.encounters (patient_key);

CREATE INDEX IF NOT EXISTS idx_curated_enc_readmitted_30d 
    ON curated.encounters (readmitted_30d);

CREATE INDEX IF NOT EXISTS idx_curated_enc_age_group 
    ON curated.encounters (age_group);

CREATE INDEX IF NOT EXISTS idx_curated_enc_admission_type 
    ON curated.encounters (admission_type);

CREATE INDEX IF NOT EXISTS idx_curated_enc_pipeline_run 
    ON curated.encounters (pipeline_run_id);

-- Curated Diagnoses Indexes
CREATE INDEX IF NOT EXISTS idx_curated_diag_encounter_key 
    ON curated.diagnoses (encounter_key);

CREATE INDEX IF NOT EXISTS idx_curated_diag_category 
    ON curated.diagnoses (diagnosis_category);

CREATE INDEX IF NOT EXISTS idx_curated_diag_position 
    ON curated.diagnoses (diagnosis_position);

-- Curated Admissions Indexes
CREATE INDEX IF NOT EXISTS idx_curated_adm_encounter_key 
    ON curated.admissions (encounter_key);

CREATE INDEX IF NOT EXISTS idx_curated_adm_patient_key 
    ON curated.admissions (patient_key);

CREATE INDEX IF NOT EXISTS idx_curated_adm_los 
    ON curated.admissions (length_of_stay);

-- Curated Readmissions Indexes
CREATE INDEX IF NOT EXISTS idx_curated_readm_encounter_key 
    ON curated.readmissions (encounter_key);

CREATE INDEX IF NOT EXISTS idx_curated_readm_status 
    ON curated.readmissions (readmission_status);

-- Staging & Rejected Indexes
CREATE INDEX IF NOT EXISTS idx_staging_encounter_id 
    ON staging.diabetic_encounters (encounter_id);

CREATE INDEX IF NOT EXISTS idx_rejected_pipeline_run 
    ON rejected.encounters (pipeline_run_id);
