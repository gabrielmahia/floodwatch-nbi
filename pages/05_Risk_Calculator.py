"""Page 5 — Risk Calculator: site-level composite flood risk scorer."""
import streamlit as st
from utils.charts import calculate_risk_score

st.set_page_config(page_title="Risk Calculator · FloodWatch NBI", page_icon="🔧", layout="wide")
st.markdown("# 🔧 Site-Level Flood Risk Calculator")
st.markdown(
    "Estimate the composite flood risk for any Nairobi location. "
    "Component weights are indicative — not calibrated to actual Nairobi hydrology. "
    "See README § 9 for calibration priorities."
)
st.caption("⚠️ DEMO — weights not validated by civil engineering or hydrological study.")

KNOWN_SITES = {
    "Custom (enter below)": None,
    "Mathare Valley (high risk)":        dict(population_density=480, drainage_coverage=12, distance_from_river_m=45,  riparian_compliant=False, slope_pct=1.5, soil_permeability=0.25),
    "Kibera Soweto East (high risk)":    dict(population_density=420, drainage_coverage=18, distance_from_river_m=80,  riparian_compliant=False, slope_pct=2.0, soil_permeability=0.30),
    "Mukuru Kwa Njenga (high risk)":     dict(population_density=390, drainage_coverage=22, distance_from_river_m=120, riparian_compliant=False, slope_pct=1.8, soil_permeability=0.28),
    "Westlands (medium risk)":           dict(population_density=85,  drainage_coverage=62, distance_from_river_m=350, riparian_compliant=True,  slope_pct=5.0, soil_permeability=0.55),
    "Karen (low risk)":                  dict(population_density=12,  drainage_coverage=78, distance_from_river_m=800, riparian_compliant=True,  slope_pct=8.5, soil_permeability=0.72),
}

with st.sidebar:
    st.markdown("## Component weights")
    st.caption("Weights sum to 100. Adjust as calibration data improves.")
    st.markdown("- Population density: **25**")
    st.markdown("- Drainage gap: **20**")
    st.markdown("- River proximity: **25**")
    st.markdown("- Riparian violation: **15**")
    st.markdown("- Flat terrain: **10**")
    st.markdown("- Soil impermeability: **5**")
    st.divider()
    st.markdown("**Extension:** Connect to NCC planning database to flag approved developments with high risk scores.")

preset = st.selectbox("Load a known site", list(KNOWN_SITES.keys()))
preset_vals = KNOWN_SITES[preset] or {}

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Site parameters")
    population_density    = st.slider("Population density (persons/hectare)", 0, 800,
                                       preset_vals.get("population_density", 150), step=10)
    drainage_coverage     = st.slider("Drainage coverage (%)", 0, 100,
                                       preset_vals.get("drainage_coverage", 40))
    distance_from_river_m = st.slider("Distance from nearest river (metres)", 0, 2000,
                                       preset_vals.get("distance_from_river_m", 300), step=25)
    riparian_compliant    = st.toggle("Riparian buffer compliant (30m setback observed)",
                                       value=preset_vals.get("riparian_compliant", True))
    slope_pct             = st.slider("Terrain slope (%)", 0.0, 30.0,
                                       preset_vals.get("slope_pct", 5.0), step=0.5)
    soil_permeability     = st.slider("Soil permeability (0=clay, 1=sandy)", 0.0, 1.0,
                                       preset_vals.get("soil_permeability", 0.4), step=0.05)

score = calculate_risk_score(
    population_density, drainage_coverage, distance_from_river_m,
    riparian_compliant, slope_pct, soil_permeability,
)

with col2:
    st.markdown("### Risk score")
    if score >= 70:
        color, label, icon = "#FF3333", "CRITICAL", "🔴"
    elif score >= 50:
        color, label, icon = "#FF6B35", "HIGH", "🟠"
    elif score >= 30:
        color, label, icon = "#FFB347", "MEDIUM", "🟡"
    else:
        color, label, icon = "#4CAF50", "LOW", "🟢"

    st.markdown(f"""
    <div style="background:#1A1F2E;border:2px solid {color};border-radius:8px;
                padding:32px;text-align:center;margin:16px 0">
      <div style="font-size:64px;margin-bottom:8px">{icon}</div>
      <div style="font-size:56px;font-weight:700;color:{color}">{score}</div>
      <div style="font-size:20px;color:{color};margin-top:4px">{label} RISK</div>
      <div style="color:#888;margin-top:12px;font-size:13px">Composite score 0–100</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Component breakdown**")
    components = [
        ("Population density",    min(population_density / 500.0, 1.0) * 25,    25),
        ("Drainage gap",          max(0, (100 - drainage_coverage) / 100.0) * 20, 20),
        ("River proximity",       max(0, 1.0 - distance_from_river_m / 500.0) * 25, 25),
        ("Riparian violation",    (1.0 if not riparian_compliant else 0.0) * 15, 15),
        ("Flat terrain",          max(0, 1.0 - slope_pct / 10.0) * 10,          10),
        ("Soil impermeability",   (1.0 - soil_permeability) * 5,                  5),
    ]
    for name, contribution, max_weight in components:
        pct = contribution / max_weight * 100 if max_weight > 0 else 0
        bar_color = "#FF3333" if pct > 70 else "#FF6B35" if pct > 40 else "#4CAF50"
        st.markdown(f"""
        <div style="margin:6px 0">
          <div style="display:flex;justify-content:space-between;font-size:13px">
            <span>{name}</span>
            <span style="color:{bar_color}">{contribution:.1f} / {max_weight}</span>
          </div>
          <div style="background:#2A2F3E;border-radius:4px;height:6px;margin-top:2px">
            <div style="background:{bar_color};width:{pct:.0f}%;height:6px;border-radius:4px"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("### Risk interpretation")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    | Score | Level | Recommended action |
    |-------|-------|-------------------|
    | 0–29  | Low   | Standard drainage maintenance |
    | 30–49 | Medium | Drainage upgrade + early warning enrollment |
    | 50–69 | High  | Resettlement risk assessment + drainage investment |
    | 70–100 | Critical | Immediate flood risk management plan required |
    """)
with col2:
    st.markdown("""
    **Priority interventions by score driver:**
    - **Proximity score dominant** → riparian buffer enforcement
    - **Drainage score dominant** → drainage infrastructure investment
    - **Density score dominant** → settlement upgrading (site and service)
    - **Riparian violation** → NCC enforcement + NEMA action
    """)
