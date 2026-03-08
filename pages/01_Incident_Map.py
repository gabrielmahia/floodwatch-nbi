"""
Page 1 — Incident Map
Select any of the 25 Kenyan cities, filter by severity/zone/enforcement,
toggle between marker map and risk heatmap.
"""
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from utils.data_loader import load_cities, load_incidents, load_all_incidents, active_cities
from utils.map_utils import build_incident_map, build_risk_heatmap

st.set_page_config(page_title="Incident Map · FloodWatch Kenya", page_icon="📍", layout="wide")
st.markdown("# 📍 Incident Map")
st.caption("⚠️ DEMO DATA — representative samples. Real sources: NCC, NDOC, Kenya Red Cross, WRMA.")

cities = active_cities()

with st.sidebar:
    st.markdown("## City")
    city_options = ["🇰🇪 All Kenya"] + [f"{c['name']} ({c['county']})" for c in cities]
    selected_label = st.selectbox("Select city", city_options)

    if selected_label == "🇰🇪 All Kenya":
        df = load_all_incidents()
        city_meta = None
        map_center = [-0.5, 37.5]
        map_zoom   = 6
    else:
        city_name = selected_label.split(" (")[0]
        city_meta = next(c for c in cities if c["name"] == city_name)
        df = load_incidents(city_meta["id"])
        map_center = [city_meta["lat"], city_meta["lon"]]
        map_zoom   = city_meta.get("zoom", 12)

    if not df.empty:
        st.divider()
        st.markdown("## Filters")
        severities = st.multiselect("Severity", ["Critical","High","Medium","Low"],
                                    default=["Critical","High","Medium","Low"])
        enforcement = st.selectbox("Policy enforcement",
                                   ["All","Not enforced only","Enforced only"])
        map_mode = st.radio("Map mode", ["Incident markers","Risk heatmap"])

if df.empty:
    st.warning("No incident data for this selection.")
    st.stop()

# Apply filters
filt = df[df["severity"].isin(severities)]
if enforcement == "Enforced only":
    filt = filt[filt["policy_enforced"] == True]
elif enforcement == "Not enforced only":
    filt = filt[filt["policy_enforced"] != True]

# KPIs
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Cities",    filt["city_name"].nunique() if "city_name" in filt.columns else 1)
c2.metric("Incidents", len(filt))
c3.metric("Deaths",    int(filt["deaths"].sum()))
c4.metric("Displaced", f"{int(filt['displaced'].sum()):,}")
c5.metric("Enforcement gap",
    int((filt["policy_existed"]==True).sum() - (filt["policy_enforced"]==True).sum()))
st.divider()

# Map
if map_mode == "Incident markers":
    m = build_incident_map(filt, center=map_center, zoom=map_zoom)
else:
    m = build_risk_heatmap(filt, center=map_center, zoom=map_zoom)
st_folium(m, width="100%", height=530, returned_objects=[])

st.divider()
st.markdown("### Incident Log")
show_cols = ["date","city_name","location","zone","severity","deaths","displaced",
             "cause","infra_damage_ksh_m","response_days","policy_existed","policy_enforced"]
show_cols = [c for c in show_cols if c in filt.columns]
st.dataframe(
    filt[show_cols].sort_values("date", ascending=False).reset_index(drop=True),
    use_container_width=True,
    column_config={
        "infra_damage_ksh_m": st.column_config.NumberColumn("Damage (KSh M)", format="%.1f"),
        "policy_existed":  st.column_config.CheckboxColumn("Policy existed"),
        "policy_enforced": st.column_config.CheckboxColumn("Policy enforced"),
    }
)
