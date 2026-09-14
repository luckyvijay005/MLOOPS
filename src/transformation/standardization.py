"""Standardization module for clinical codes and encounter attributes.

Maps numeric identifiers (admission type, discharge disposition, admission source)
and standardizes ICD-9 diagnosis codes into clinical diagnostic categories
following the protocol published with the UCI Diabetes dataset (Strack et al., 2014).
"""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger


# Default dictionary mappings based on official IDs_mapping.csv
ADMISSION_TYPE_MAP = {
    1: "Emergency",
    2: "Urgent",
    3: "Elective",
    4: "Newborn",
    5: "Not Available",
    6: "NULL",
    7: "Trauma Center",
    8: "Not Mapped",
}

DISCHARGE_DISPOSITION_MAP = {
    1: "Discharged to home",
    2: "Discharged/transferred to another short term hospital",
    3: "Discharged/transferred to SNF",
    4: "Discharged/transferred to ICF",
    5: "Discharged/transferred to another type of inpatient care institution",
    6: "Discharged/transferred to home with home health service",
    7: "Left AMA",
    11: "Expired",
    13: "Hospice / home",
    14: "Hospice / medical facility",
    18: "NULL",
    19: "Expired at home. Medicaid only, hospice",
    20: "Expired in a medical facility. Medicaid only, hospice",
    21: "Expired, place unknown. Medicaid only, hospice",
    22: "Discharged/transferred to another rehab facility",
    25: "Not Mapped",
}

ADMISSION_SOURCE_MAP = {
    1: "Physician Referral",
    2: "Clinic Referral",
    3: "HMO Referral",
    4: "Transfer from a hospital",
    5: "Transfer from a Skilled Nursing Facility (SNF)",
    6: "Transfer from another health care facility",
    7: "Emergency Room",
    17: "NULL",
    20: "Not Mapped",
}


def load_id_mappings_from_csv(mapping_file: Optional[Path] = None) -> tuple[dict, dict, dict]:
    """Loads mappings from IDs_mapping.csv if present, falling back to built-ins."""
    path = mapping_file or Config.MAPPING_PATH
    if not path.exists():
        return ADMISSION_TYPE_MAP, DISCHARGE_DISPOSITION_MAP, ADMISSION_SOURCE_MAP

    adm_type, disch_disp, adm_src = {}, {}, {}
    curr_dict = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if "admission_type_id" in line:
                    curr_dict = adm_type
                    continue
                elif "discharge_disposition_id" in line:
                    curr_dict = disch_disp
                    continue
                elif "admission_source_id" in line:
                    curr_dict = adm_src
                    continue

                if curr_dict is not None and "," in line:
                    parts = line.split(",", 1)
                    try:
                        k = int(parts[0].strip())
                        v = parts[1].strip()
                        curr_dict[k] = v
                    except ValueError:
                        pass
        return (
            adm_type or ADMISSION_TYPE_MAP,
            disch_disp or DISCHARGE_DISPOSITION_MAP,
            adm_src or ADMISSION_SOURCE_MAP,
        )
    except Exception as exc:
        logger.warning(f"Could not parse {path}: {exc}. Using built-in maps.")
        return ADMISSION_TYPE_MAP, DISCHARGE_DISPOSITION_MAP, ADMISSION_SOURCE_MAP


def categorize_icd9(icd_code: Optional[str]) -> str:
    """Categorizes an ICD-9 diagnosis code into broad clinical categories.

    Categories based on Strack et al. (2014) standard mapping:
      - Circulatory: 390–459, 785
      - Respiratory: 460–519, 786
      - Digestive: 520–579, 787
      - Diabetes: 250.xx
      - Injury: 800–999
      - Musculoskeletal: 710–739
      - Genitourinary: 580–629, 788
      - Neoplasms: 140–239
      - Other: all others or external causes (E/V codes)
    """
    if pd.isna(icd_code) or not icd_code:
        return "Missing/Unknown"

    code_str = str(icd_code).strip()
    if code_str in ["?", "None", "nan", ""]:
        return "Missing/Unknown"

    # Diabetes specific check
    if code_str.startswith("250"):
        return "Diabetes"

    # E and V codes (supplementary classification of external causes and factors)
    if code_str.startswith(("V", "E")):
        return "Other"

    # Numeric range parsing
    try:
        # Extract leading numeric portion before decimal
        numeric_part = float(code_str.split(".")[0])
        int_code = int(numeric_part)

        if (390 <= int_code <= 459) or int_code == 785:
            return "Circulatory"
        elif (460 <= int_code <= 519) or int_code == 786:
            return "Respiratory"
        elif (520 <= int_code <= 579) or int_code == 787:
            return "Digestive"
        elif (800 <= int_code <= 999):
            return "Injury and Poisoning"
        elif (710 <= int_code <= 739):
            return "Musculoskeletal"
        elif (580 <= int_code <= 629) or int_code == 788:
            return "Genitourinary"
        elif (140 <= int_code <= 239):
            return "Neoplasms"
        else:
            return "Other"
    except ValueError:
        return "Other"


def standardize_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes encounter metadata, lookup IDs, and adds diagnosis categories."""
    df_std = df.copy()

    adm_type_map, disch_disp_map, adm_src_map = load_id_mappings_from_csv()

    # Safely convert lookup IDs to integer and map to string descriptions
    def safe_map(series, mapping, default="Unknown"):
        numeric_series = pd.to_numeric(series, errors="coerce").fillna(-1).astype(int)
        return numeric_series.map(lambda k: mapping.get(k, default))

    df_std["admission_type"] = safe_map(df_std["admission_type_id"], adm_type_map, "Unknown Admission")
    df_std["discharge_disposition"] = safe_map(df_std["discharge_disposition_id"], disch_disp_map, "Unknown Disposition")
    df_std["admission_source"] = safe_map(df_std["admission_source_id"], adm_src_map, "Unknown Source")

    # Standardize and categorize diag_1, diag_2, diag_3
    df_std["diag_1_category"] = df_std["diag_1"].apply(categorize_icd9)
    df_std["diag_2_category"] = df_std["diag_2"].apply(categorize_icd9)
    df_std["diag_3_category"] = df_std["diag_3"].apply(categorize_icd9)

    return df_std
