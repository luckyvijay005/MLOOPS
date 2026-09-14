"""Synthetic sample dataset generator for development and unit testing.

IMPORTANT:
This script produces SYNTHETIC TEST DATA — NOT REAL PATIENT DATA.
All patient IDs, encounters, and clinical records are randomly synthesized
to mirror the exact schema and data quirks of the UCI 130-US Hospitals dataset.
"""

import sys
from pathlib import Path
import random
import pandas as pd
import numpy as np

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils.config import Config
from src.utils.logger import logger


def generate_synthetic_dataset(num_records: int = 500, output_path: Path | None = None) -> Path:
    """Generates a synthetic diabetic encounter dataset matching the UCI schema."""
    if output_path is None:
        output_path = Config.SAMPLE_DATA_DIR / "synthetic_diabetic_data.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    logger.info(f"Generating {num_records} synthetic diabetic encounters...")

    races = ["Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other", "?"]
    genders = ["Female", "Male", "Unknown/Invalid"]
    age_brackets = [
        "[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
        "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"
    ]
    admission_type_ids = [1, 2, 3, 4, 5, 6, 7, 8]  # 1=Emergency, 2=Urgent, 3=Elective, etc.
    discharge_disposition_ids = [1, 2, 3, 4, 5, 6, 7, 11, 13, 14, 18, 22, 25]  # 1=Home, etc.
    admission_source_ids = [1, 2, 3, 4, 5, 6, 7, 17, 20]  # 7=Emergency Room, etc.
    payer_codes = ["MC", "MD", "HM", "UN", "BC", "SP", "CP", "DM", "CM", "?"]
    medical_specialties = [
        "InternalMedicine", "Cardiology", "Family/GeneralPractice",
        "Surgery-General", "Emergency/Trauma", "Orthopedics", "Nephrology", "?"
    ]
    medication_options = ["No", "Steady", "Up", "Down"]
    readmitted_options = ["<30", ">30", "NO"]

    # Sample ICD-9 codes representative of the dataset
    icd_circulatory = ["401", "410", "414", "428", "427"]
    icd_respiratory = ["466", "482", "486", "491", "493"]
    icd_digestive = ["530", "560", "571", "574", "577"]
    icd_diabetes = ["250.00", "250.01", "250.02", "250.6", "250.8"]
    icd_injury = ["800", "820", "824", "996"]
    icd_other = ["276", "290", "599", "682", "707", "780", "?"]

    all_icd = icd_circulatory + icd_respiratory + icd_digestive + icd_diabetes + icd_injury + icd_other

    # Pool of 300 unique synthetic patients to simulate readmissions
    patient_pool = [random.randint(10000000, 99999999) for _ in range(max(10, num_records // 2))]

    rows = []
    for i in range(num_records):
        encounter_id = 100000 + i
        patient_nbr = random.choice(patient_pool)
        
        race = random.choices(races, weights=[0.70, 0.18, 0.05, 0.02, 0.02, 0.03])[0]
        gender = random.choices(genders, weights=[0.53, 0.46, 0.01])[0]
        age = random.choices(age_brackets, weights=[0.01, 0.01, 0.02, 0.05, 0.10, 0.22, 0.32, 0.20, 0.06, 0.01])[0]
        weight = "?" if random.random() < 0.96 else "[75-100)"

        admission_type_id = random.choice(admission_type_ids)
        discharge_disposition_id = random.choice(discharge_disposition_ids)
        admission_source_id = random.choice(admission_source_ids)
        
        time_in_hospital = random.randint(1, 14)
        payer_code = random.choice(payer_codes)
        medical_specialty = random.choice(medical_specialties)

        num_lab_procedures = random.randint(1, 120)
        num_procedures = random.randint(0, 6)
        num_medications = random.randint(1, 45)
        number_outpatient = random.choices([0, 1, 2, 3], weights=[0.85, 0.10, 0.03, 0.02])[0]
        number_emergency = random.choices([0, 1, 2, 3], weights=[0.88, 0.08, 0.03, 0.01])[0]
        number_inpatient = random.choices([0, 1, 2, 3], weights=[0.70, 0.20, 0.07, 0.03])[0]

        diag_1 = random.choice(all_icd)
        diag_2 = random.choice(all_icd)
        diag_3 = random.choice(all_icd)
        number_diagnoses = random.randint(1, 9)

        max_glu_serum = random.choices(["None", "Norm", ">200", ">300"], weights=[0.94, 0.02, 0.02, 0.02])[0]
        a1cresult = random.choices(["None", "Norm", ">7", ">8"], weights=[0.82, 0.05, 0.04, 0.09])[0]

        # 23 medications
        meds = {
            "metformin": random.choices(medication_options, weights=[0.80, 0.18, 0.01, 0.01])[0],
            "repaglinide": random.choices(medication_options, weights=[0.98, 0.015, 0.002, 0.003])[0],
            "nateglinide": "No",
            "chlorpropamide": "No",
            "glimepiride": random.choices(medication_options, weights=[0.94, 0.05, 0.005, 0.005])[0],
            "acetohexamide": "No",
            "glipizide": random.choices(medication_options, weights=[0.87, 0.11, 0.01, 0.01])[0],
            "glyburide": random.choices(medication_options, weights=[0.89, 0.09, 0.01, 0.01])[0],
            "tolbutamide": "No",
            "pioglitazone": random.choices(medication_options, weights=[0.92, 0.07, 0.005, 0.005])[0],
            "rosiglitazone": random.choices(medication_options, weights=[0.93, 0.06, 0.005, 0.005])[0],
            "acarbose": "No",
            "miglitol": "No",
            "troglitazone": "No",
            "tolazamide": "No",
            "examide": "No",
            "citagliptin": "No",
            "insulin": random.choices(medication_options, weights=[0.45, 0.30, 0.13, 0.12])[0],
            "glyburide-metformin": "No",
            "glipizide-metformin": "No",
            "glimepiride-pioglitazone": "No",
            "metformin-rosiglitazone": "No",
            "metformin-pioglitazone": "No",
        }

        change = "Ch" if any(v in ["Up", "Down"] for v in meds.values()) else "No"
        diabetesmed = "Yes" if any(v != "No" for v in meds.values()) else "No"

        # Readmission target: roughly 11% <30, 35% >30, 54% NO (reflecting UCI distribution)
        readmitted = random.choices(readmitted_options, weights=[0.11, 0.35, 0.54])[0]

        row = {
            "encounter_id": encounter_id,
            "patient_nbr": patient_nbr,
            "race": race,
            "gender": gender,
            "age": age,
            "weight": weight,
            "admission_type_id": admission_type_id,
            "discharge_disposition_id": discharge_disposition_id,
            "admission_source_id": admission_source_id,
            "time_in_hospital": time_in_hospital,
            "payer_code": payer_code,
            "medical_specialty": medical_specialty,
            "num_lab_procedures": num_lab_procedures,
            "num_procedures": num_procedures,
            "num_medications": num_medications,
            "number_outpatient": number_outpatient,
            "number_emergency": number_emergency,
            "number_inpatient": number_inpatient,
            "diag_1": diag_1,
            "diag_2": diag_2,
            "diag_3": diag_3,
            "number_diagnoses": number_diagnoses,
            "max_glu_serum": max_glu_serum,
            "A1Cresult": a1cresult,
            **meds,
            "change": change,
            "diabetesMed": diabetesmed,
            "readmitted": readmitted,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic dataset successfully written to {output_path} ({len(df)} rows, {len(df.columns)} columns)")
    return output_path


def generate_synthetic_id_mapping(output_path: Path | None = None) -> Path:
    """Generates standard IDs_mapping.csv matching the UCI dataset."""
    if output_path is None:
        output_path = Config.RAW_DATA_DIR / "IDs_mapping.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_content = """admission_type_id,description
1,Emergency
2,Urgent
3,Elective
4,Newborn
5,Not Available
6,NULL
7,Trauma Center
8,Not Mapped

discharge_disposition_id,description
1,Discharged to home
2,Discharged/transferred to another short term hospital
3,Discharged/transferred to SNF
4,Discharged/transferred to ICF
5,Discharged/transferred to another type of inpatient care institution
6,Discharged/transferred to home with home health service
7,Left AMA
11,Expired
13,Hospice / home
14,Hospice / medical facility
18,NULL
22,Discharged/transferred to another rehab facility
25,Not Mapped

admission_source_id,description
1,Physician Referral
2,Clinic Referral
3,HMO Referral
4,Transfer from a hospital
5,Transfer from a Skilled Nursing Facility (SNF)
6,Transfer from another health care facility
7,Emergency Room
17,NULL
20,Not Mapped
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mapping_content)
    logger.info(f"IDs_mapping.csv written to {output_path}")
    return output_path


if __name__ == "__main__":
    generate_synthetic_dataset(num_records=500)
    generate_synthetic_id_mapping()
