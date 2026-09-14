# Hospital Readmission Analytics and Prediction Using Public Data

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8+-017CEE.svg)](https://airflow.apache.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-FF4B4B.svg)](https://streamlit.io/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## 1. Project Overview
This repository contains **Part 1** of a production-style academic data engineering project titled:

> **"Hospital Readmission Analytics and Prediction Using Public Data"**

Using only de-identified public healthcare data from the **UCI Diabetes 130-US Hospitals (1999–2008)** repository, this project establishes:
- A reproducible 12-task ETL pipeline (orchestrated via **Apache Airflow** and standalone CLI).
- A HIPAA Safe Harbor-compliant de-identification layer using **cryptographically salted SHA-256 surrogate keys**.
- An audited **PostgreSQL analytical database** featuring staging, curated relational tables, error quarantine, and pre-aggregated data marts.
- A comprehensive **Data Quality (DQ) validation framework** tracking nullity, duplicate encounters, and clinical bounds.
- An interactive **Streamlit & Plotly analytics dashboard** with 5 analytical views, dynamic filters, and observational cohort rankings.
- A clean, modular boundary prepared for **Part 2: Predictive Machine Learning & MLOps**.

---

## 2. System Architecture

```
Public UCI Dataset (101,766 Encounters)
        │
        ▼
Local Secure Landing Zone (SHA-256 Checksum & Metadata Log)
        │
        ▼
Staging Layer (staging.diabetic_encounters)
        │
        ▼
Data Quality & Validation Gate ──[Failed Records]──► Rejected Layer (rejected.encounters)
        │ (Passed Records)
        ▼
Curated Relational Layer (PostgreSQL / Salted SHA-256 Privacy Shield)
├── curated.encounters
├── curated.diagnoses (ICD-9 Categorization)
├── curated.admissions
└── curated.readmissions
        │
        ▼
Analytical Data Marts (Pre-Aggregated Summary Tables)
├── analytics.patient_summary (1 row per patient key)
├── analytics.readmission_summary
├── analytics.admission_summary
├── analytics.diagnosis_summary
└── analytics.length_of_stay_summary
        │
        ▼
Interactive Presentation Tier (Streamlit Dashboard & Plotly Visualizations)
```

*(See [diagrams/architecture.mmd](diagrams/architecture.mmd) for the complete architecture diagram, including the Part 2 MLOps extension roadmap).*

---

## 3. Technology Stack

| Component | Technology | Version / Specification |
| :--- | :--- | :--- |
| **Language** | Python | 3.11+ |
| **Data Processing** | Pandas, NumPy, PyArrow | 2.1+, 1.26+, 14.0+ |
| **Orchestration** | Apache Airflow / Standalone CLI Runner | 12 modular idempotent tasks |
| **Relational Database** | PostgreSQL, SQLAlchemy, Psycopg2-binary | PostgreSQL 16, SQLAlchemy 2.0+ |
| **Dashboard** | Streamlit, Plotly Express & Graph Objects | Streamlit 1.31+, Plotly 5.18+ |
| **Data Quality & Testing**| Pytest, Pytest-mock, Pydantic | Pytest 7.4+, 18 unit tests |
| **Containerization** | Docker, Docker Compose | PostgreSQL 16 Alpine + Streamlit container |

---

## 4. Dataset Source & Attribution

- **Dataset:** Diabetes 130-US Hospitals for Years 1999–2008 (UCI ML Repository ID: 296).
- **Investigators:** Beata Strack, Jonathan P. DeShazo, Chris McGuinness, Thelma Cupp, Paul L. Cios, John N. Clore (2014).
- **Scale:** `101,766` hospital encounters across `71,518` unique patients; 50 clinical features.
- **Target Label:**
  - `<30`: Readmission within 30 days (`readmitted_30d = 1`, ~11.16% frequency).
  - `>30`: Readmission after 30 days (`readmitted_30d = 0`, ~34.93% frequency).
  - `NO`: No readmission observed (`readmitted_30d = 0`, ~53.91% frequency).
- **Provenance Documentation:** Detailed in [docs/dataset_source.md](docs/dataset_source.md).

---

## 5. Patient Privacy & Ethical Safeguards

1. **HIPAA Safe Harbor Compliance:** Uses only public, de-identified data. No direct identifiers (names, SSNs, phone numbers, addresses, DOB) exist.
2. **Salted Cryptographic Hashing:**
   $$\text{patient\_key} = \text{SHA-256}(\text{patient\_nbr} + \text{PROJECT\_PATIENT\_SALT})$$
3. **Identifier Purging:** Raw `patient_nbr` is completely dropped during feature engineering and never persisted into curated or analytical tables.
4. **Causation vs. Correlation:** Observational cohort frequencies are explicitly separated from clinical predictive risk.

---

## 6. Project Directory Structure

```text
hospital-readmission-analytics/
├── .env.example                # Environment configuration template
├── .env                        # Local active environment variables
├── .gitignore                  # Git exclude patterns
├── requirements.txt            # Pinned dependencies
├── docker-compose.yml          # PostgreSQL & Dashboard container definitions
├── Dockerfile.dashboard        # Streamlit container build specification
├── Makefile                    # Automation shortcuts
│
├── data/
│   ├── raw/                    # Raw immutable CSVs (diabetic_data.csv, IDs_mapping.csv)
│   ├── staging/                # Staged Parquet files with ingestion audit metadata
│   ├── cleaned/                # Curated Parquet relational entities & analytics cache
│   ├── rejected/               # Quarantined invalid/duplicate encounters
│   └── sample/                 # Synthetic test dataset (500 records)
│
├── airflow/
│   ├── dags/
│   │   └── hospital_readmission_etl.py  # 12-task Airflow DAG definition
│   ├── logs/
│   └── plugins/
│
├── src/
│   ├── ingestion/
│   │   ├── download_dataset.py # Automated archive download & extraction
│   │   └── ingest.py           # Checksum, audit logging, & staging loader
│   ├── transformation/
│   │   ├── clean_data.py       # Missing values & readmission normalization
│   │   ├── validate_data.py    # Schema, bounds, duplicate checks & rejection routing
│   │   ├── standardization.py  # Lookup decoders & ICD-9 clinical categorizer
│   │   └── feature_engineering.py # Salted surrogate keys & relational splitting
│   ├── database/
│   │   ├── connection.py       # SQLAlchemy engine & health check
│   │   ├── create_schema.py    # Idempotent DDL migration runner
│   │   └── load_postgres.py    # Bulk database loader & analytical mart calculator
│   └── utils/
│       ├── config.py           # Environment & path configuration
│       └── logger.py           # Structured privacy-safe logging
│
├── sql/
│   ├── 01_create_schemas.sql   # Creates metadata, staging, rejected, curated, analytics
│   ├── 02_create_tables.sql    # DDL for all relational and summary tables
│   ├── 03_create_indexes.sql   # Performance B-Tree indexes
│   ├── 04_create_views.sql     # Executive KPI and cohort ranking views
│   └── 05_analytics_queries.sql # 10 optimized analytical benchmark queries
│
├── dashboard/
│   ├── app.py                  # Main Streamlit application
│   ├── components/
│   │   ├── kpi_cards.py        # Executive metric cards
│   │   └── charts.py           # Plotly interactive visualizations
│   └── queries/
│       └── data_loader.py      # Resilient dual-backend data loader
│
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_ingestion.py       # Checksum, file detection, & metadata tests
│   ├── test_validation.py      # Schema, null, bound, & duplicate rejection tests
│   ├── test_transformations.py # Missing codes, age grouping, ICD-9 & surrogate tests
│   └── test_database.py        # DDL existence, offline resilience & mart tests
│
├── docs/
│   ├── architecture.md         # Detailed architectural documentation
│   ├── data_dictionary.md      # Comprehensive field definitions & classifications
│   ├── validation_rules.md     # Formal 18-rule data quality specification
│   ├── dataset_source.md       # Provenance, license, & access guide
│   └── pipeline_flow.md        # 12-stage ETL orchestration guide
│
├── diagrams/
│   └── architecture.mmd        # Mermaid diagram (Part 1 & Future Part 2)
│
├── reports/
│   ├── execution_evidence.md   # Screenshot capture guide & reproduction proof
│   ├── project_report_outline.md # 8-10 page academic course report outline
│   └── pipeline_run_summary_*.md # Automated execution summary reports
│
└── scripts/
    ├── run_pipeline.py         # End-to-end ETL CLI orchestrator
    ├── run_dashboard.py        # Streamlit dashboard launch shortcut
    └── generate_sample_data.py # Synthetic 500-encounter test data generator
```

---

## 7. Installation & Quick Start

### Step 1: Clone Repository & Create Virtual Environment
```bash
# Clone repository
git clone <repository-url>
cd hospital-readmission-analytics

# Windows 11 PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` (already pre-configured for local development):
```bash
cp .env.example .env
```

---

## 8. Running Ingestion & ETL Pipeline

### Option A: Complete Pipeline on Official UCI Dataset (Recommended)
This command automatically downloads the official 101,766-row UCI dataset if missing, computes SHA-256 checksums, performs data quality gating, and builds all analytical data marts in ~20 seconds:
```bash
python scripts/run_pipeline.py
```

### Option B: Pipeline on Synthetic Sample Data
If working completely offline or developing tests:
```bash
python scripts/generate_sample_data.py
python scripts/run_pipeline.py --dataset-path data/sample/synthetic_diabetic_data.csv
```

---

## 9. Launching the Interactive Streamlit Dashboard

Run the dashboard:
```bash
python scripts/run_dashboard.py
```
*Or directly via Streamlit:*
```bash
streamlit run dashboard/app.py
```
Open your browser at: **`http://localhost:8501`**

### Dashboard Features:
- **Executive KPI Banner:** Total Encounters, Unique Patients, 30-Day Readmission Rate, Average Length of Stay, Average Medications.
- **View 1 — Readmission by Age:** Dual-axis chart with volume bars and readmission percentage lines.
- **View 2 — Readmission by Diagnosis:** Sortable horizontal bar chart across categorized ICD-9 clinical groupings.
- **View 3 — Length of Stay:** Inpatient duration distribution and readmission frequency correlation.
- **View 4 — Admission Patterns:** Hierarchical breakdown of admission types and discharge dispositions.
- **View 5 — Cohort Analysis:** Dynamic sidebar filters (Age, Gender, Race, Admission Type, Readmission Status) with cross-tabulation.
- **Special View — Observed High-Readmission Cohorts:** Ranks historical sub-cohorts with minimum sample size controls ($N \ge 50$ or $N \ge 100$) with causation disclaimer.
- **Data & Privacy Policy:** Transparent documentation of the SHA-256 surrogate shield and HIPAA alignment.

---

## 10. Running Automated Tests

Run the full Pytest suite:
```bash
python -m pytest tests/ -v
```
**Result:** 18 passing unit and integration tests covering:
- Dataset existence and SHA-256 verification.
- Schema validation and missing column detection.
- Primary key nullity and duplicate encounter rejection.
- Numeric bound enforcement ($LOS \ge 0$).
- Missing value code normalization (`'?'` $\rightarrow$ `NULL`).
- Readmission binary encoding (`<30` $\rightarrow$ 1, `>30`/`NO` $\rightarrow$ 0).
- Salted SHA-256 surrogate patient key generation.
- ICD-9 diagnosis categorization into clinical groups.
- PostgreSQL DDL script integrity and offline cache fallback.

---

## 11. PostgreSQL Database & Docker Compose

To run a persistent PostgreSQL 16 database using Docker Compose:
```bash
# Start PostgreSQL
docker compose up -d postgres

# Initialize schema manually (if running outside pipeline)
python src/database/create_schema.py

# Stop PostgreSQL
docker compose down
```

*Note: The platform is architected with dual-backend resilience. If PostgreSQL is not active, the pipeline and dashboard automatically utilize the high-availability local Parquet data marts in `data/cleaned/`!*

---

## 12. Apache Airflow Orchestration

The Airflow DAG is defined in [`airflow/dags/hospital_readmission_etl.py`](airflow/dags/hospital_readmission_etl.py).

To execute via Apache Airflow:
1. Ensure your Airflow environment is active (`export AIRFLOW_HOME=$(pwd)/airflow`).
2. Verify DAG integrity:
   ```bash
   python airflow/dags/hospital_readmission_etl.py
   ```
3. Trigger the DAG:
   ```bash
   airflow dags trigger hospital_readmission_etl
   ```

---

## 13. Part 2 MLOps Extension Roadmap

Part 1 establishes a clean foundation for Part 2 without polluting Part 1 with incomplete ML models:
1. **Feature Store:** Pre-engineered relational tables (`curated.encounters`, `curated.diagnoses`, `analytics.patient_summary`) can be queried directly to generate training datasets.
2. **Algorithms for Part 2:** Logistic Regression (baseline), Random Forest, and XGBoost/LightGBM.
3. **Experiment Tracking:** MLflow tracking for hyperparameters, ROC-AUC, and precision-recall curves.
4. **Inference Service:** FastAPI container serving real-time risk predictions to the Streamlit application.

---

## 14. Academic & Healthcare Disclaimer
This project was constructed solely for academic and educational purposes as Part 1 of a Data Engineering and MLOps curriculum. All analyses are observational. The observational associations between patient features and readmission frequencies do **not** represent clinical risk scores, medical advice, or causal relationships.
