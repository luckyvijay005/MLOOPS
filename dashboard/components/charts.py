"""Plotly Chart generation components for Hospital Readmission Analytics Dashboard."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Standard cohesive palette
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#ff7f0e"
ACCENT_RED = "#d62728"
ACCENT_GREEN = "#2ca02c"
COLOR_PALETTE = ["#2b5c8f", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d"]


def plot_readmission_by_age(df: pd.DataFrame) -> go.Figure:
    """Creates a dual-axis chart: Total Volume (bars) and 30-Day Readmission Rate (line)."""
    if df.empty or "age_group" not in df.columns:
        return go.Figure()

    grp = df.groupby("age_group").agg(
        total_encounters=("encounter_key", "count"),
        readmitted_30d=("readmitted_30d", "sum"),
        rate=("readmitted_30d", lambda x: x.mean() * 100),
    ).reset_index()

    # Sort in clinical age order
    order_map = {"<30": 1, "30-50": 2, "50-70": 3, "70+": 4, "Unknown": 5}
    grp["sort_order"] = grp["age_group"].map(lambda x: order_map.get(x, 99))
    grp = grp.sort_values("sort_order")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Volume Bar
    fig.add_trace(
        go.Bar(
            x=grp["age_group"],
            y=grp["total_encounters"],
            name="Encounter Volume",
            marker_color="#3366cc",
            opacity=0.8,
            hovertemplate="Age Group: %{x}<br>Encounters: %{y:,}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Rate Line
    fig.add_trace(
        go.Scatter(
            x=grp["age_group"],
            y=grp["rate"],
            name="30-Day Readmission Rate (%)",
            mode="lines+markers+text",
            text=grp["rate"].apply(lambda v: f"{v:.1f}%"),
            textposition="top center",
            line=dict(color="#dc3912", width=3),
            marker=dict(size=8),
            hovertemplate="Age Group: %{x}<br>Readmission Rate: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="<b>30-Day Readmission Rate and Encounter Volume by Age Group</b>",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(title_text="Standardized Age Group")
    fig.update_yaxes(title_text="Total Encounters", secondary_y=False)
    fig.update_yaxes(title_text="30-Day Readmission Rate (%)", secondary_y=True, rangemode="tozero")

    return fig


def plot_readmission_by_diagnosis(df_diag: pd.DataFrame, sort_by: str = "Readmission Rate") -> go.Figure:
    """Horizontal bar chart showing readmission rate by clinical diagnosis category."""
    if df_diag.empty or "diagnosis_category" not in df_diag.columns or "readmitted_30d" not in df_diag.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No diagnosis data available for the selected cohort.",
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        return fig

    grp = df_diag.groupby("diagnosis_category").agg(
        total_diagnoses=("diagnosis_key", "count"),
        readmitted_30d=("readmitted_30d", "sum"),
        rate=("readmitted_30d", lambda x: x.mean() * 100),
    ).reset_index()

    if sort_by == "Readmission Rate":
        grp = grp.sort_values("rate", ascending=True)
    else:
        grp = grp.sort_values("total_diagnoses", ascending=True)

    fig = px.bar(
        grp,
        x="rate",
        y="diagnosis_category",
        orientation="h",
        text=grp["rate"].apply(lambda v: f"{v:.1f}%"),
        labels={"rate": "30-Day Readmission Rate (%)", "diagnosis_category": "Diagnosis Category"},
        title=f"<b>Observed 30-Day Readmission Rate by Diagnosis Category (Sorted by {sort_by})</b>",
        color="rate",
        color_continuous_scale="Reds",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="Category: %{y}<br>Readmission Rate: %{x:.2f}%<extra></extra>",
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        coloraxis_showscale=False,
    )
    return fig


def plot_length_of_stay(df: pd.DataFrame) -> go.Figure:
    """Length of stay distribution and relationship with 30-day readmissions."""
    if df.empty or "time_in_hospital" not in df.columns:
        return go.Figure()

    grp = df.groupby("time_in_hospital").agg(
        total_encounters=("encounter_key", "count"),
        readmissions_30d=("readmitted_30d", "sum"),
        rate=("readmitted_30d", lambda x: x.mean() * 100),
    ).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=grp["time_in_hospital"],
            y=grp["total_encounters"],
            name="Encounters",
            marker_color="#5b92e5",
            opacity=0.7,
            hovertemplate="Length of Stay: %{x} days<br>Volume: %{y:,}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=grp["time_in_hospital"],
            y=grp["rate"],
            name="30-Day Readmission Rate (%)",
            mode="lines+markers",
            line=dict(color="#b22222", width=3),
            hovertemplate="Length of Stay: %{x} days<br>Readmission Rate: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="<b>Length of Stay Distribution & Readmission Association</b>",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(title_text="Length of Stay (Days)", dtick=1)
    fig.update_yaxes(title_text="Encounter Volume", secondary_y=False)
    fig.update_yaxes(title_text="30-Day Readmission Rate (%)", secondary_y=True)

    return fig


def plot_admission_patterns(df: pd.DataFrame) -> go.Figure:
    """Sunburst / hierarchical breakdown of admission types and discharge dispositions."""
    if df.empty or "admission_type" not in df.columns:
        return go.Figure()

    top_types = df["admission_type"].value_counts().nlargest(4).index
    df_filtered = df[df["admission_type"].isin(top_types)].copy()
    top_disch = df_filtered["discharge_disposition"].value_counts().nlargest(5).index
    df_filtered = df_filtered[df_filtered["discharge_disposition"].isin(top_disch)]

    fig = px.sunburst(
        df_filtered,
        path=["admission_type", "discharge_disposition"],
        values="readmitted_30d",
        color="readmitted_30d",
        color_continuous_scale="Blues",
        title="<b>Hierarchical Admission Type & Discharge Disposition Breakdown</b>",
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def plot_high_readmission_cohorts(df: pd.DataFrame, min_encounters: int = 100) -> go.Figure:
    """Ranks sub-cohorts by observed historical 30-day readmission rate with sample threshold."""
    if df.empty or "age_group" not in df.columns:
        return go.Figure()

    grp = df.groupby(["age_group", "gender", "admission_type"]).agg(
        cohort_size=("encounter_key", "count"),
        readmissions=("readmitted_30d", "sum"),
        rate=("readmitted_30d", lambda x: x.mean() * 100),
    ).reset_index()

    # Filter out small cohorts to prevent misleading sample artifacts
    grp = grp[grp["cohort_size"] >= min_encounters]
    grp["cohort_label"] = (
        grp["age_group"].astype(str) + " | " + grp["gender"].astype(str) + " | " + grp["admission_type"].astype(str)
    )
    top_cohorts = grp.sort_values("rate", ascending=True).tail(15)

    if top_cohorts.empty:
        # If threshold too high for sample data, show notice figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"No cohorts meet the minimum threshold of {min_encounters} encounters in current data.",
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        return fig

    top_cohorts["label_text"] = top_cohorts.apply(
        lambda r: f"{r['rate']:.1f}% (N={int(r['cohort_size']):,})", axis=1
    )

    fig = px.bar(
        top_cohorts,
        x="rate",
        y="cohort_label",
        orientation="h",
        text="label_text",
        labels={"rate": "Observed 30-Day Readmission Rate (%)", "cohort_label": "Cohort (Age | Gender | Admission Type)"},
        title=f"<b>Observed High-Readmission Cohorts (Minimum {min_encounters} Encounters)</b>",
        color="rate",
        color_continuous_scale="Oranges",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        coloraxis_showscale=False,
    )
    return fig
