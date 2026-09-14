"""Hospital Readmission Analytics Dashboard.

Interactive academic analytics dashboard built with Streamlit and Plotly.
Provides 5 analytical views, KPI metrics, observed high-readmission cohorts,
and healthcare data privacy assurances.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils.config import Config
from dashboard.queries.data_loader import load_data_from_db_or_cache, compute_kpis
from dashboard.components.kpi_cards import render_kpi_metrics
from dashboard.components.charts import (
    plot_readmission_by_age,
    plot_readmission_by_diagnosis,
    plot_length_of_stay,
    plot_admission_patterns,
    plot_high_readmission_cohorts,
)

# Set page configuration
st.set_page_config(
    page_title="Hospital Readmission Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .disclaimer-box {
        background-color: #f7fafc;
        border-left: 4px solid #3182ce;
        padding: 0.9rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">🏥 Hospital Readmission Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Part 1: Healthcare Data Engineering, Analytical Marts & Observational Readmission Patterns (UCI Diabetes 130-US Hospitals)</div>',
        unsafe_allow_html=True,
    )

    # 1. Load Data
    with st.spinner("Loading analytical data..."):
        df_encounters, marts = load_data_from_db_or_cache()

    if df_encounters is None or df_encounters.empty:
        st.warning("No data found! Please execute the pipeline runner first using `python scripts/run_pipeline.py`.")
        st.stop()

    # 2. Sidebar Controls & Global Filters
    st.sidebar.header("🔍 Cohort Filters")
    st.sidebar.caption("Filter encounters dynamically across views:")

    # Age Filter
    all_ages = sorted([str(x) for x in df_encounters["age_group"].dropna().unique()])
    selected_ages = st.sidebar.multiselect("Age Groups", options=all_ages, default=all_ages)

    # Gender Filter
    all_genders = sorted([str(x) for x in df_encounters["gender"].dropna().unique()])
    selected_genders = st.sidebar.multiselect("Gender", options=all_genders, default=all_genders)

    # Race Filter
    all_races = sorted([str(x) for x in df_encounters["race"].dropna().unique()])
    selected_races = st.sidebar.multiselect("Race / Ethnicity", options=all_races, default=all_races)

    # Admission Type Filter
    all_adm_types = sorted([str(x) for x in df_encounters["admission_type"].dropna().unique()])
    selected_adm_types = st.sidebar.multiselect("Admission Type", options=all_adm_types, default=all_adm_types)

    # Readmission Status Filter
    all_readm_status = sorted([str(x) for x in df_encounters["readmission_status"].dropna().unique()])
    selected_readm_status = st.sidebar.multiselect("Readmission Status", options=all_readm_status, default=all_readm_status)

    # Apply Filters
    df_filtered = df_encounters[
        df_encounters["age_group"].isin(selected_ages)
        & df_encounters["gender"].isin(selected_genders)
        & df_encounters["race"].isin(selected_races)
        & df_encounters["admission_type"].isin(selected_adm_types)
        & df_encounters["readmission_status"].isin(selected_readm_status)
    ]

    st.sidebar.divider()
    st.sidebar.markdown(f"**Filtered Volume:** {len(df_filtered):,} / {len(df_encounters):,} encounters")

    # 3. Top-Level KPI Summary Banner
    kpis = compute_kpis(df_filtered)
    render_kpi_metrics(kpis)

    st.markdown("---")

    # 4. Tabbed Views
    tabs = st.tabs([
        "📊 View 1: Age Analysis",
        "🩺 View 2: Diagnosis Categories",
        "⏱️ View 3: Length of Stay",
        "🚪 View 4: Admission Patterns",
        "👥 View 5: Cohort Analysis",
        "⚠️ High-Readmission Cohorts",
        "🔒 Data & Privacy Policy",
    ])

    # View 1: Readmission by Age
    with tabs[0]:
        st.subheader("30-Day Readmission Rates Across Age Groups")
        st.caption("Evaluates volume of admissions and percentage readmitted within 30 days.")
        fig_age = plot_readmission_by_age(df_filtered)
        st.plotly_chart(fig_age, use_container_width=True)

    # View 2: Readmission by Diagnosis
    with tabs[1]:
        st.subheader("Readmission Rates by Clinical Diagnosis Category")
        st.caption("ICD-9 codes categorized following the standard protocol (Circulatory, Respiratory, Diabetes, etc.).")
        sort_col, _ = st.columns([2, 4])
        with sort_col:
            sort_choice = st.radio("Sort categories by:", ["Readmission Rate", "Total Volume"], horizontal=True)

        # Get diagnoses dataframe and join readmitted_30d outcome from active filtered encounters
        diag_path = Config.CLEANED_DATA_DIR / "curated_diagnoses_latest.parquet"
        if diag_path.exists() and not df_filtered.empty:
            df_diag_all = pd.read_parquet(diag_path)
            # Filter to active encounter keys and join readmission outcome
            df_diag_filtered = df_diag_all.merge(
                df_filtered[["encounter_key", "readmitted_30d"]],
                on="encounter_key",
                how="inner",
            )
        else:
            df_diag_filtered = pd.DataFrame()

        fig_diag = plot_readmission_by_diagnosis(df_diag_filtered, sort_by=sort_choice)
        st.plotly_chart(fig_diag, use_container_width=True)

    # View 3: Length of Stay
    with tabs[2]:
        st.subheader("Hospital Length of Stay (LOS) Dynamics")
        st.caption("Distribution of patient days in hospital and observed readmission correlation.")
        fig_los = plot_length_of_stay(df_filtered)
        st.plotly_chart(fig_los, use_container_width=True)

    # View 4: Admission Patterns
    with tabs[3]:
        st.subheader("Admission Sources & Discharge Dispositions")
        st.caption("Hierarchical breakdown of encounter pathways from intake to discharge.")
        fig_adm = plot_admission_patterns(df_filtered)
        st.plotly_chart(fig_adm, use_container_width=True)

    # View 5: Cohort Analysis
    with tabs[4]:
        st.subheader("Dynamic Multi-Dimensional Cohort Breakdown")
        st.caption("Deep-dive into filtered patient sub-populations with comparative metrics.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Readmission Distribution")
            status_counts = df_filtered["readmission_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Encounters"]
            import plotly.express as px
            fig_pie = px.pie(
                status_counts,
                names="Status",
                values="Encounters",
                color="Status",
                color_discrete_map={"<30": "#d62728", ">30": "#ff7f0e", "NO": "#2ca02c"},
                hole=0.4,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            st.markdown("#### Gender & Readmission Cross-Tabulation")
            ct = pd.crosstab(
                df_filtered["gender"],
                df_filtered["readmission_status"],
                normalize="index"
            ) * 100
            st.dataframe(ct.round(2).style.format("{:.2f}%"), use_container_width=True)

    # Special View: Observed High-Readmission Cohorts
    with tabs[5]:
        st.subheader("Observed High-Readmission Cohorts (Observational Analytics)")
        st.markdown("""
        <div class="disclaimer-box">
            <b>⚠️ Academic & Clinical Disclaimer:</b><br>
            The cohorts listed below represent historical combinations with higher observed 30-day readmission frequencies. 
            <b>This is NOT an ML predictive risk score.</b> Historical observational association does not imply clinical risk, individual prognosis, or causation.
        </div>
        """, unsafe_allow_html=True)

        min_sample = st.slider("Minimum Cohort Sample Size Threshold (N):", min_value=10, max_value=500, value=50, step=10)
        fig_cohorts = plot_high_readmission_cohorts(df_filtered, min_encounters=min_sample)
        st.plotly_chart(fig_cohorts, use_container_width=True)

    # Data & Privacy Policy
    with tabs[6]:
        st.subheader("Healthcare Data Privacy & Governance")
        st.markdown(f"""
        ### Public & De-Identified Dataset
        - **Source:** UCI Machine Learning Repository — *Diabetes 130-US Hospitals (1999-2008)*.
        - **Original Investigators:** Beata Strack, Jonathan P. DeShazo, Chris McGuinness, et al. (2014).
        - **Privacy Guarantee:** The underlying dataset is completely de-identified. No HIPAA direct identifiers (names, SSNs, phone numbers, addresses, DOB) exist in the source data.

        ### Cryptographic Surrogate Shield
        - **Patient Key Hashing:** All original patient numbers are transformed into cryptographically salted SHA-256 surrogate keys:
          `patient_key = SHA-256(patient_nbr + salt)`
        - **Re-Identification Prevention:** The original `patient_nbr` is completely dropped during feature engineering and never reaches the analytical data mart or dashboard.
        - **Educational Scope:** This project is Part 1 of an academic Data Engineering and MLOps course. Results are intended strictly for educational analysis.
        """)


if __name__ == "__main__":
    main()
