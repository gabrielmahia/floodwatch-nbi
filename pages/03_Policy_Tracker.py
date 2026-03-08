"""FloodWatch NBI - Page 03: Policy Tracker."""
from pathlib import Path
import pandas as pd
import streamlit as st
from utils.charts import (
    policy_status_donut, budget_gap_chart,
    blocking_factor_bar, lives_at_risk_bar,
)

st.set_page_config(page_title="Policy Tracker - FloodWatch NBI", page_icon="policy", layout="wide")
st.title("Policy Tracker")
st.caption("10 flood-relevant policies tracked across status, budget utilisation, and blocking factors.")

ROOT = Path(__file__).parent.parent

@st.cache_data
def load():
    return pd.read_csv(ROOT / "data" / "policies.csv")

df = load()

STATUS_COLORS = {
    "Completed": "#22C55E",
    "Partially Implemented": "#3B82F6",
    "Stalled": "#EAB308",
    "Not Enforced": "#F97316",
    "Not Started": "#EF4444",
    "Draft Only": "#A855F7",
}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total policies tracked", len(df))
col2.metric("Completed",
    len(df[df["status"] == "Completed"]),
    f"{len(df[df['status']=='Completed'])/len(df)*100:.0f}%")
col3.metric("Total allocated (KSh M)", f"{df['budget_allocated_ksh_m'].sum():,.0f}")
col4.metric("Lives at risk (unimplemented)",
    f"{df[df['status']!='Completed']['lives_saved_estimate'].sum():,}")

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(policy_status_donut(df), use_container_width=True)
with col_b:
    st.plotly_chart(blocking_factor_bar(df), use_container_width=True)

st.divider()
st.plotly_chart(budget_gap_chart(df), use_container_width=True)

st.divider()
st.plotly_chart(lives_at_risk_bar(df), use_container_width=True)

st.divider()
st.markdown("### Policy Detail")
status_filter = st.multiselect("Filter by status",
    options=list(df["status"].unique()),
    default=list(df["status"].unique()))
filtered = df[df["status"].isin(status_filter)]

for _, row in filtered.iterrows():
    color = STATUS_COLORS.get(row["status"], "#94A3B8")
    utilized_ksh = row["budget_allocated_ksh_m"] * row["budget_utilized_pct"] / 100
    with st.expander(f"{row['policy_id']} — {row['name']} [{row['status']}]"):
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Status:** :{color.lstrip('#')}[{row['status']}]")
        c2.markdown(f"**Implementing body:** {row['implementing_body']}")
        c3.markdown(f"**Since:** {row['year_recommended']} ({row['source']})")
        st.markdown(f"**Budget:** KSh {row['budget_allocated_ksh_m']:.0f}M allocated · "
                    f"KSh {utilized_ksh:.0f}M utilised ({row['budget_utilized_pct']:.0f}%)")
        st.markdown(f"**Blocker:** {row['blocking_factor']}")
        st.markdown(f"**Lives saved if implemented:** ~{row['lives_saved_estimate']:,}")
        st.markdown(f"**Notes:** {row['notes']}")
