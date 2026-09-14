# Dataset Source & Provenance Documentation

## 1. Overview
- **Dataset Title:** Diabetes 130-US Hospitals for Years 1999–2008
- **Repository:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008)
- **Repository ID:** 296
- **Primary Investigators & Citation:** 
  > Beata Strack, Jonathan P. DeShazo, Chris McGuinness, Thelma Cupp, Paul L. Cios, and John N. Clore. *"Impact of HbA1c Measurement on Hospital Readmission Rates: Analysis of 70,000 Clinical Database Patient Records."* BioMed Research International, vol. 2014, Article ID 781670, 11 pages, 2014. DOI: [10.1155/2014/781670](https://doi.org/10.1155/2014/781670).
- **License / Terms of Use:** Creative Commons Attribution 4.0 International (CC BY 4.0). De-identified public research database.

---

## 2. Dataset Purpose & Context
The dataset represents 10 years (1999–2008) of clinical care at 130 US hospitals and integrated delivery networks. It was constructed to investigate whether the measurement of hemoglobin A1c (HbA1c) during hospitalization influenced 30-day diabetic patient readmission rates.

---

## 3. Cohort Inclusion Criteria
The encounters satisfy the following clinical inclusion criteria:
1. It is an **inpatient encounter** (a hospital admission).
2. It is a **diabetic encounter**, defined as an encounter where diabetes was entered into the system as any of the primary, secondary, or tertiary diagnoses.
3. The length of hospital stay was at least **1 day** and at most **14 days**.
4. Laboratory tests were performed during the encounter.
5. Medications were administered during the encounter.

---

## 4. Dataset Dimensions & Attributes
- **Total Encounter Records:** `101,766`
- **Unique Patients:** `71,518` (some patients experienced multiple encounters over the 10-year observation window).
- **Total Features / Columns:** `50`
- **Primary Target Variable:** `readmitted`
  - `<30`: Patient was readmitted within 30 days of discharge (~11.16% of encounters).
  - `>30`: Patient was readmitted after more than 30 days (~34.93% of encounters).
  - `NO`: No readmission recorded in the observation window (~53.91% of encounters).

---

## 5. De-Identification & Privacy Characteristics
- The source dataset was thoroughly de-identified under the Health Insurance Portability and Accountability Act (HIPAA) Safe Harbor method prior to deposition in the UCI Repository.
- No direct identifiers are present: no patient names, postal addresses, telephone numbers, Social Security Numbers, medical record numbers, or dates of birth.
- Patient ages are aggregated into 10-year categorical brackets (e.g., `[50-60)`).
- Hospital identifiers are omitted; data is pooled across 130 institutions.
- In this pipeline, the source `patient_nbr` is further transformed using a cryptographically salted SHA-256 surrogate hash (`patient_key = SHA-256(patient_nbr + salt)`), and the raw `patient_nbr` is strictly discarded from all downstream analytical tables and dashboards.

---

## 6. Access & Download Instructions
The dataset is bundled as a zip file containing `diabetic_data.csv` and `IDs_mapping.csv`.

- **Direct Download URL:**
  `https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip`
- **Automated Download:** Run:
  ```bash
  python src/ingestion/download_dataset.py
  ```
- **Manual Placement:** If downloading manually, extract `diabetic_data.csv` and `IDs_mapping.csv` directly into the `data/raw/` folder.
