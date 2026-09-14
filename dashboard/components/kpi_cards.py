"""Reusable KPI Cards Component with modern medical-analytics styling."""

import streamlit as st


def render_kpi_metrics(kpis: dict):
    """Renders 5 top-level KPI cards with modern UI cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Encounters",
            value=f"{kpis['total_encounters']:,}",
            help="Total number of qualified inpatient hospital encounters evaluated.",
        )

    with col2:
        st.metric(
            label="Unique Patients",
            value=f"{kpis['unique_patients']:,}",
            help="Distinct de-identified patient surrogate keys in this population.",
        )

    with col3:
        st.metric(
            label="30-Day Readmission Rate",
            value=f"{kpis['readmission_rate_30d']:.2f}%",
            help="Percentage of encounters resulting in readmission within 30 days (<30 category).",
        )

    with col4:
        st.metric(
            label="Avg Length of Stay",
            value=f"{kpis['avg_length_of_stay']:.1f} days",
            help="Average duration in hospital per inpatient encounter.",
        )

    with col5:
        st.metric(
            label="Avg Medications",
            value=f"{kpis['avg_medications']:.1f}",
            help="Average number of distinct medications administered during hospitalization.",
        )
