"""Page 4 — City Benchmarks: Kenya cities vs global resilience comparators."""
import streamlit as st
import json
import pandas as pd
from utils.charts import resilience_radar, deaths_per_event_scatter, dark_layout
import plotly.express as px

st.set_page_config(page_title="City Benchmarks · FloodWatch Kenya", page_icon="🌍", layout="wide")
st.markdown("# 🌍 City Benchmarks")
st.markdown(
    "Kenyan cities measured against global flood resilience comparators. "
    "Nairobi is the reference point; Medellin is the relevant analogue; "
    "Rotterdam is the ceiling; Dhaka is the warning."
)
st.caption("⚠️ Resilience scores are manually curated composites — see README for methodology.")

@st.cache_data
def load():
    with open("data/city_benchmarks.json") as f:
        return json.load(f)["cities"]

cities = load()

STATUS_LABELS = {
    "current":  ("🔴","Current state — Nairobi"),
    "analogue": ("🟡","Relevant analogue"),
    "ceiling":  ("🟢","Ceiling case"),
    "warning":  ("⚫","Warning trajectory"),
}

with st.sidebar:
    st.markdown("## City selection")
    selected_names = st.multiselect("Compare cities",
                                     [c["name"] for c in cities],
                                     default=[c["name"] for c in cities])
    selected = [c for c in cities if c["name"] in selected_names]
    st.divider()
    for key,(icon,label) in STATUS_LABELS.items():
        st.markdown(f"{icon} {label}")
    st.divider()
    st.markdown("**Design note:** The city benchmark is diagnostic, not aspirational. Medellin — messy, under-resourced, made progress through political will — is the actionable analogue for Nairobi.")

if not selected:
    st.warning("Select at least one city.")
    st.stop()

c1,c2 = st.columns(2)
with c1:
    st.plotly_chart(resilience_radar(selected), use_container_width=True)
with c2:
    st.plotly_chart(deaths_per_event_scatter(selected), use_container_width=True)

st.divider()
st.markdown("### City profiles")
for city in selected:
    icon,_ = STATUS_LABELS.get(city.get("status",""),("⚪",""))
    color  = city.get("color","#888")
    years  = city.get("years_to_resilience")
    years_str = f"{years} years from start" if years else "trajectory unclear"
    with st.expander(f"{icon} **{city['name']}, {city['country']}** — Score: {city['resilience_score']}/100"):
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Resilience score", city["resilience_score"])
        c2.metric("Deaths/event avg",  city["deaths_per_event_avg"])
        c3.metric("Riparian compliance",f"{city['riparian_compliance_pct']}%")
        c4.metric("Flood budget/capita",f"USD {city['flood_budget_usd_per_capita']:.0f}")
        cc1,cc2 = st.columns(2)
        with cc1:
            st.markdown(f"**Drainage:** {city['drainage_coverage_pct']}%")
            st.markdown(f"**Early warning:** {city['early_warning_hours']}h")
            st.markdown(f"**Flood-vulnerable:** {city['flood_vulnerable_pct']}%")
            st.markdown(f"**Time to current resilience:** {years_str}")
        with cc2:
            st.markdown(f"**Key intervention:**\n{city['key_intervention']}")
            st.markdown(f"**Political enabler:**\n{city['political_enabler']}")
        if city.get("transferable"):
            st.markdown("**Transferable to Nairobi / Kenya:**")
            for l in city["transferable"]:
                st.markdown(f"- {l}")

st.divider()
df = pd.DataFrame(selected)
st.markdown("### Raw comparison table")
show = ["name","country","resilience_score","deaths_per_event_avg",
        "riparian_compliance_pct","drainage_coverage_pct",
        "early_warning_hours","flood_budget_usd_per_capita"]
st.dataframe(df[show].set_index("name"), use_container_width=True)
