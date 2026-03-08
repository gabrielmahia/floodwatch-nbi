"""FloodWatch NBI - Page 05: Risk Calculator."""
import streamlit as st
from utils.charts import calculate_risk_score, risk_gauge

st.set_page_config(page_title="Risk Calculator - FloodWatch NBI", page_icon="risk", layout="wide")
st.title("Site-Level Flood Risk Calculator")
st.markdown(
    "Composite flood risk score for a specific site. "
    "Component weights are approximate — not calibrated to Nairobi hydrology. "
    "Partner with JKUAT/UoN civil engineering for calibration (see HANDOFF.md §11)."
)
st.caption("DEMO MODEL - scores are illustrative. Do not use for planning decisions without expert calibration.")

col_inputs, col_output = st.columns([2, 3])

with col_inputs:
    st.markdown("### Site parameters")

    pop_density = st.slider(
        "Population density (persons/hectare)",
        min_value=0, max_value=500, value=150, step=10,
        help="Nairobi average ~45 · Mathare ~350 · Runda ~8",
    )
    drainage = st.slider(
        "Drainage coverage (%)",
        min_value=0, max_value=100, value=40, step=5,
        help="Nairobi city average ~34%",
    )
    river_dist = st.slider(
        "Distance from nearest river (metres)",
        min_value=0, max_value=1000, value=200, step=10,
        help="30m = riparian reserve boundary under Water Act 2016",
    )
    riparian = st.checkbox(
        "Within riparian reserve (30m buffer)?",
        value=False,
        help="Structures within the 30m reserve violate NEMA/WRMA regulations",
    )
    slope = st.slider(
        "Terrain slope (%)",
        min_value=0, max_value=30, value=3, step=1,
        help="Flat Nairobi basin ~1-3% · Ngong hills ~15-25%",
    )
    soil = st.slider(
        "Soil permeability (0 = clay · 1 = sandy)",
        min_value=0.0, max_value=1.0, value=0.3, step=0.05,
        help="Black cotton soil (common in Nairobi) ~0.1-0.2",
    )

with col_output:
    score = calculate_risk_score(
        population_density=pop_density,
        drainage_coverage=drainage,
        distance_from_river_m=river_dist,
        riparian_compliant=riparian,
        slope_pct=slope,
        soil_permeability=soil,
    )
    st.plotly_chart(risk_gauge(score), use_container_width=True)

    st.markdown("### Component breakdown")
    density_s  = min(pop_density / 500, 1.0) * 25
    drainage_s = (1 - min(drainage, 100) / 100) * 20
    proximity_s = max(0, 1 - river_dist / 500) * 25
    riparian_s  = 15 if riparian else 0
    terrain_s   = max(0, 1 - slope / 20) * 10
    soil_s      = (1 - min(soil, 1.0)) * 5

    components = {
        "Population density (max 25)": round(density_s, 1),
        "Drainage gap (max 20)":        round(drainage_s, 1),
        "River proximity (max 25)":     round(proximity_s, 1),
        "Riparian violation (max 15)":  round(riparian_s, 1),
        "Terrain flatness (max 10)":    round(terrain_s, 1),
        "Soil impermeability (max 5)":  round(soil_s, 1),
    }
    for label, val in components.items():
        max_val = int(label.split("max ")[1].rstrip(")"))
        pct = val / max_val if max_val > 0 else 0
        bar_color = "#EF4444" if pct > 0.7 else "#EAB308" if pct > 0.4 else "#22C55E"
        st.markdown(
            f"**{label}**: {val} "
            f"<div style=\"width:{pct*100:.0f}%;height:6px;background:{bar_color};border-radius:3px;\"></div>",
            unsafe_allow_html=True,
        )

st.divider()
st.markdown("### Reference sites (estimated)")
refs = [
    ("Mathare Valley core",     350, 15,  50, True,  1, 0.15),
    ("Mukuru kwa Njenga",       280, 20,  80, True,  1, 0.20),
    ("Kibera Sector 5",         300, 18,  40, False, 2, 0.18),
    ("South B (formal estate)", 80,  70, 300, False, 3, 0.40),
    ("Karen residential",       15,  95, 800, False, 8, 0.60),
]
import pandas as pd
ref_df = pd.DataFrame(refs, columns=[
    "Site", "Density", "Drainage%", "River_m", "Riparian", "Slope%", "Soil"
])
ref_df["Risk Score"] = ref_df.apply(
    lambda r: calculate_risk_score(r["Density"], r["Drainage%"],
                                    r["River_m"], r["Riparian"],
                                    r["Slope%"], r["Soil"]), axis=1
)
st.dataframe(ref_df[["Site", "Risk Score", "Density", "Drainage%", "River_m"]],
             use_container_width=True)
