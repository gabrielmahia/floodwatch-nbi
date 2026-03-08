"""FloodWatch NBI - Page 02: Impact Analysis."""
from pathlib import Path
import pandas as pd
import streamlit as st
from utils.charts import (
    zone_impact_bar, seasonality_chart, cause_treemap,
    enforcement_gap_chart, dark_layout,
)
import plotly.express as px

st.set_page_config(page_title="Impact Analysis - FloodWatch NBI", page_icon="chart", layout="wide")
st.title("Impact Analysis")
st.caption("DEMO DATA - 15 sampled incidents. Analysis understates true scale.")

ROOT = Path(__file__).parent.parent

@st.cache_data
def load():
    df = pd.read_csv(ROOT / "data" / "incidents.csv", parse_dates=["date"])
    df["policy_existed"]  = df["policy_existed"].astype(bool)
    df["policy_enforced"] = df["policy_enforced"].astype(bool)
    return df

df = load()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(zone_impact_bar(df), use_container_width=True)
with col2:
    st.plotly_chart(seasonality_chart(df), use_container_width=True)

st.divider()
col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(cause_treemap(df), use_container_width=True)
with col4:
    st.plotly_chart(enforcement_gap_chart(df), use_container_width=True)

st.divider()
st.markdown("### Enforcement Gap — Detailed View")
st.markdown(
    "The enforcement gap is the central accountability signal. "
    "Each row below represents an incident where policy existed but was not enforced."
)
gap_df = df[df["policy_existed"] & ~df["policy_enforced"]]
gap_pct = len(gap_df) / len(df) * 100
c1, c2, c3 = st.columns(3)
c1.metric("Enforcement gap incidents", len(gap_df), f"{gap_pct:.0f}% of total")
c2.metric("Deaths in gap incidents", int(gap_df["deaths"].sum()))
c3.metric("Displaced in gap incidents", f"{int(gap_df['displaced'].sum()):,}")

st.dataframe(gap_df[["date","location","zone","severity","deaths",
                       "displaced","cause","response_days"]].assign(
    date=gap_df["date"].dt.strftime("%Y-%m-%d")
), use_container_width=True)
