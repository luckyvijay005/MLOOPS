"""Feature Engineering and Privacy Shield module.

Enforces strict de-identification via salted SHA-256 surrogate hashing,
engineers clinical variables (age groups, length of stay, prior admission counts),
and normalizes the dataset into relational entities (encounters, diagnoses, admissions, readmissions).
"""

import sys
import hashlib
from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import numpy as np

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from src.transformation.standardization import categorize_icd9


def generate_surrogate_key(raw_id: str, salt: str | None = None, prefix: str = "") -> str:
    """Generates a deterministic SHA-256 salted surrogate hash."""
    active_salt = salt or Config.PATIENT_SALT
    combined = f"{prefix}{str(raw_id).strip()}_{active_salt}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def map_age_group(age_bracket: str | None) -> str:
    """Maps 10-year age brackets into clinically meaningful standardized age groups.

    Standardized Groups:
      - '<30':  [0-10), [10-20), [20-30)
      - '30-50': [30-40), [40-50)
      - '50-70': [50-60), [60-70)
      - '70+':   [70-80), [80-90), [90-100)
    """
    if pd.isna(age_bracket):
        return "Unknown"
    
    bracket = str(age_bracket).strip()
    if bracket in ["[0-10)", "[10-20)", "[20-30)"]:
        return "<30"
    elif bracket in ["[30-40)", "[40-50)"]:
        return "30-50"
    elif bracket in ["[50-60)", "[60-70)"]:
        return "50-70"
    elif bracket in ["[70-80)", "[80-90)", "[90-100)"]:
        return "70+"
    return "Unknown"


class FeatureEngineer:
    """Computes analytical features and creates normalized relational entities."""

    def __init__(self, run_id: str = "DEFAULT_RUN"):
        self.run_id = run_id

    def engineer_features(self, df_cleaned: pd.DataFrame) -> pd.DataFrame:
        """Applies privacy shield hashing and creates core engineered features."""
        logger.info(f"[{self.run_id}] Engineering features and privacy surrogate keys...")
        df_feat = df_cleaned.copy()

        # 1. Privacy Shield: Generate surrogate keys and strip raw identifiers
        df_feat["patient_key"] = df_feat["patient_nbr"].apply(
            lambda x: generate_surrogate_key(x, prefix="PAT_")
        )
        df_feat["encounter_key"] = df_feat["encounter_id"].apply(
            lambda x: generate_surrogate_key(x, prefix="ENC_")
        )
        df_feat["encounter_id_surrogate"] = df_feat["encounter_key"].str[:16]

        # Defensive handling of readmission status if raw dataframe was passed
        if "readmission_status" not in df_feat.columns:
            if "readmitted" in df_feat.columns:
                raw_readm = df_feat["readmitted"].fillna("NO").astype(str).str.strip()
                df_feat["readmission_status"] = raw_readm.map(lambda s: s if s in ["<30", ">30", "NO"] else "NO")
                df_feat["readmitted_30d"] = (df_feat["readmission_status"] == "<30").astype(int)
            else:
                df_feat["readmission_status"] = "NO"
                df_feat["readmitted_30d"] = 0

        # Defensive lookup fallbacks if standardization was skipped in test
        if "admission_type" not in df_feat.columns and "admission_type_id" in df_feat.columns:
            from src.transformation.standardization import ADMISSION_TYPE_MAP
            df_feat["admission_type"] = pd.to_numeric(df_feat["admission_type_id"], errors="coerce").map(
                lambda k: ADMISSION_TYPE_MAP.get(k, "Unknown")
            )
        if "discharge_disposition" not in df_feat.columns and "discharge_disposition_id" in df_feat.columns:
            from src.transformation.standardization import DISCHARGE_DISPOSITION_MAP
            df_feat["discharge_disposition"] = pd.to_numeric(df_feat["discharge_disposition_id"], errors="coerce").map(
                lambda k: DISCHARGE_DISPOSITION_MAP.get(k, "Unknown")
            )
        if "admission_source" not in df_feat.columns and "admission_source_id" in df_feat.columns:
            from src.transformation.standardization import ADMISSION_SOURCE_MAP
            df_feat["admission_source"] = pd.to_numeric(df_feat["admission_source_id"], errors="coerce").map(
                lambda k: ADMISSION_SOURCE_MAP.get(k, "Unknown")
            )

        # 2. Clinical Engineered Features
        df_feat["age_group"] = df_feat["age"].apply(map_age_group)
        
        # Numeric conversions with robust coercion
        df_feat["time_in_hospital"] = pd.to_numeric(df_feat["time_in_hospital"], errors="coerce").fillna(1).astype(int)
        df_feat["length_of_stay"] = df_feat["time_in_hospital"]

        df_feat["num_lab_procedures"] = pd.to_numeric(df_feat["num_lab_procedures"], errors="coerce").fillna(0).astype(int)
        df_feat["num_procedures"] = pd.to_numeric(df_feat["num_procedures"], errors="coerce").fillna(0).astype(int)
        df_feat["num_medications"] = pd.to_numeric(df_feat["num_medications"], errors="coerce").fillna(0).astype(int)
        df_feat["medication_count"] = df_feat["num_medications"]

        df_feat["number_outpatient"] = pd.to_numeric(df_feat["number_outpatient"], errors="coerce").fillna(0).astype(int)
        df_feat["prior_outpatient_visits"] = df_feat["number_outpatient"]

        df_feat["number_emergency"] = pd.to_numeric(df_feat["number_emergency"], errors="coerce").fillna(0).astype(int)
        df_feat["prior_emergency_visits"] = df_feat["number_emergency"]

        df_feat["number_inpatient"] = pd.to_numeric(df_feat["number_inpatient"], errors="coerce").fillna(0).astype(int)
        df_feat["prior_inpatient_visits"] = df_feat["number_inpatient"]

        df_feat["number_diagnoses"] = pd.to_numeric(df_feat["number_diagnoses"], errors="coerce").fillna(0).astype(int)
        df_feat["diagnosis_count"] = df_feat["number_diagnoses"]

        # Drop original raw patient_nbr to guarantee privacy
        if "patient_nbr" in df_feat.columns:
            df_feat = df_feat.drop(columns=["patient_nbr"])

        return df_feat

    def build_relational_tables(self, df_feat: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Decomposes the engineered dataset into normalized relational tables."""
        logger.info(f"[{self.run_id}] Normalizing into relational entities...")

        # 1. Curated Encounters
        enc_cols = [
            "encounter_key",
            "patient_key",
            "encounter_id_surrogate",
            "age_group",
            "gender",
            "race",
            "admission_type",
            "discharge_disposition",
            "admission_source",
            "time_in_hospital",
            "num_lab_procedures",
            "num_procedures",
            "num_medications",
            "number_outpatient",
            "number_emergency",
            "number_inpatient",
            "number_diagnoses",
            "readmission_status",
            "readmitted_30d",
        ]
        available_enc_cols = [c for c in enc_cols if c in df_feat.columns]
        df_encounters = df_feat[available_enc_cols].copy()
        if "gender" in df_encounters.columns:
            df_encounters["gender"] = df_encounters["gender"].fillna("Unknown")
        df_encounters["pipeline_run_id"] = self.run_id

        # 2. Curated Diagnoses (Unpivoted diag_1, diag_2, diag_3)
        diag_records = []
        for _, row in df_feat.iterrows():
            enc_key = row["encounter_key"]
            for pos in [1, 2, 3]:
                code_col = f"diag_{pos}"
                if code_col in row and pd.notna(row[code_col]):
                    code = str(row[code_col]).strip()
                    category = categorize_icd9(code)
                    diag_key = hashlib.sha256(f"{enc_key}_diag_{pos}".encode("utf-8")).hexdigest()[:32]
                    diag_records.append({
                        "diagnosis_key": diag_key,
                        "encounter_key": enc_key,
                        "diagnosis_position": pos,
                        "diagnosis_code": code,
                        "diagnosis_category": category,
                    })
        df_diagnoses = pd.DataFrame(diag_records)

        # 3. Curated Admissions
        adm_records = []
        for _, row in df_feat.iterrows():
            enc_key = row["encounter_key"]
            adm_key = hashlib.sha256(f"{enc_key}_adm".encode("utf-8")).hexdigest()[:32]
            adm_records.append({
                "admission_key": adm_key,
                "encounter_key": enc_key,
                "patient_key": row["patient_key"],
                "admission_type": row.get("admission_type", "Unknown"),
                "admission_source": row.get("admission_source", "Unknown"),
                "discharge_disposition": row.get("discharge_disposition", "Unknown"),
                "admission_sequence": 1,
                "length_of_stay": row["length_of_stay"],
                "prior_outpatient_visits": row["prior_outpatient_visits"],
                "prior_emergency_visits": row["prior_emergency_visits"],
                "prior_inpatient_visits": row["prior_inpatient_visits"],
            })
        df_admissions = pd.DataFrame(adm_records)

        # 4. Curated Readmissions
        readm_records = []
        for _, row in df_feat.iterrows():
            enc_key = row["encounter_key"]
            readm_key = hashlib.sha256(f"{enc_key}_readm".encode("utf-8")).hexdigest()[:32]
            status = row["readmission_status"]
            category = "Readmitted < 30 Days" if status == "<30" else ("Readmitted > 30 Days" if status == ">30" else "No Readmission")
            readm_records.append({
                "readmission_key": readm_key,
                "encounter_key": enc_key,
                "patient_key": row["patient_key"],
                "readmission_status": status,
                "readmitted_30d": row["readmitted_30d"],
                "readmission_category": category,
            })
        df_readmissions = pd.DataFrame(readm_records)

        logger.info(
            f"[{self.run_id}] Relational entities built: {len(df_encounters)} encounters, "
            f"{len(df_diagnoses)} diagnoses, {len(df_admissions)} admissions, {len(df_readmissions)} readmissions."
        )

        return {
            "encounters": df_encounters,
            "diagnoses": df_diagnoses,
            "admissions": df_admissions,
            "readmissions": df_readmissions,
        }

    def generate_patient_summary(self, df_encounters: pd.DataFrame) -> pd.DataFrame:
        """Aggregates multi-encounter patient summary table."""
        logger.info(f"[{self.run_id}] Computing patient summary analytical aggregation...")

        agg_dict = {
            "encounter_key": "count",
            "number_inpatient": "sum",
            "number_emergency": "sum",
            "number_outpatient": "sum",
            "time_in_hospital": "mean",
            "num_medications": "mean",
            "number_diagnoses": "mean",
            "readmitted_30d": ["sum", "mean"],
        }

        grouped = df_encounters.groupby("patient_key").agg(agg_dict)  # type: ignore[arg-type]
        grouped.columns = [
            "total_encounters",
            "total_inpatient_visits",
            "total_emergency_visits",
            "total_outpatient_visits",
            "average_length_of_stay",
            "average_medications",
            "average_diagnoses",
            "number_of_readmissions",
            "readmission_rate",
        ]
        df_patient_summary = grouped.reset_index()

        df_patient_summary["average_length_of_stay"] = df_patient_summary["average_length_of_stay"].round(2)
        df_patient_summary["average_medications"] = df_patient_summary["average_medications"].round(2)
        df_patient_summary["average_diagnoses"] = df_patient_summary["average_diagnoses"].round(2)
        df_patient_summary["readmission_rate"] = df_patient_summary["readmission_rate"].round(4)
        df_patient_summary["first_encounter_los"] = None
        df_patient_summary["last_encounter_los"] = None

        logger.info(f"[{self.run_id}] Patient summary created for {len(df_patient_summary)} unique patients.")
        return df_patient_summary

    def persist_curated_data(self, tables: Dict[str, pd.DataFrame]) -> None:
        """Persists curated relational entities to local storage (Parquet)."""
        Config.CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        for name, table in tables.items():
            path = Config.CLEANED_DATA_DIR / f"curated_{name}_{self.run_id}.parquet"
            latest_path = Config.CLEANED_DATA_DIR / f"curated_{name}_latest.parquet"
            table.to_parquet(path, index=False)
            table.to_parquet(latest_path, index=False)
        logger.info(f"[{self.run_id}] All curated tables saved to {Config.CLEANED_DATA_DIR}")
