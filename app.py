"""
FloodWatch Kenya — Urban flood resilience intelligence for Kenya.
Landing page: national KPI summary, city coverage map, alert banner.

Data compiled from NDOC situation reports, Kenya Red Cross field reports, NCC drainage audits, NEMA enforcement records, and county government documentation.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_all_incidents, load_all_policies, load_cities, active_cities
from utils.charts import dark_layout

st.set_page_config(
    page_title="FloodWatch Kenya",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def get_all_data():
    incidents = load_all_incidents()
    policies  = load_all_policies()
    return incidents, policies

incidents, policies = get_all_data()
cities = active_cities()

# ── Alert banner ──────────────────────────────────────────────────────────────
ALERT_ACTIVE  = True
ALERT_LEVEL   = "HIGH"
ALERT_MESSAGE = "Long-rains season active (March–June). Garissa Tana River watch active. Budalangi Nzoia River pre-flood conditions. Nairobi and Kisumu drainage clearance operations underway."

if ALERT_ACTIVE:
    color = {"HIGH": "#FF6B35", "CRITICAL": "#FF3333", "WATCH": "#FFB347"}.get(ALERT_LEVEL, "#FF6B35")
    st.markdown(f"""
    <div style="background:{color}22;border-left:4px solid {color};padding:12px 16px;
                border-radius:4px;margin-bottom:16px;">
      <span style="color:{color};font-weight:700">⚠ FLOOD ALERT — {ALERT_LEVEL}</span>
      <span style="color:#E8E8E8;margin-left:12px">{ALERT_MESSAGE}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🌊 FloodWatch Kenya")
st.markdown(
    f"Urban flood resilience intelligence across **{len(cities)} Kenyan cities**. "
    "Tracking incidents, policy accountability, and the enforcement gap."
)

st.divider()

# ── National KPIs ─────────────────────────────────────────────────────────────
total_deaths     = int(incidents["deaths"].sum()) if not incidents.empty else 0
total_displaced  = int(incidents["displaced"].sum()) if not incidents.empty else 0
total_incidents  = len(incidents)
policy_gap       = int(
    (incidents["policy_existed"] == True).sum() -
    (incidents["policy_enforced"] == True).sum()
) if not incidents.empty else 0

total_policies   = len(policies) if not policies.empty else 0
lives_at_risk    = int(pd.to_numeric(policies.loc[policies["status"] != "Completed", "lives_saved_estimate"], errors="coerce").fillna(0).sum()) if not policies.empty else 0
budget_alloc     = pd.to_numeric(policies["budget_allocated_ksh_m"], errors="coerce").fillna(0).sum() if not policies.empty else 0
budget_used      = (pd.to_numeric(policies["budget_allocated_ksh_m"], errors="coerce").fillna(0) * pd.to_numeric(policies["budget_utilized_pct"], errors="coerce").fillna(0) / 100).sum() if not policies.empty else 0
budget_idle_pct  = round((1 - budget_used / budget_alloc) * 100, 1) if budget_alloc else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Cities tracked", len(cities))
col2.metric("Incidents (sampled)", total_incidents)
col3.metric("Deaths (sampled)", f"{total_deaths:,}")
col4.metric("Displaced (sampled)", f"{total_displaced:,}")
col5.metric("Enforcement gap", policy_gap, help="Incidents where policy existed but not enforced")
col6.metric("Lives at risk (policy gap)", f"{lives_at_risk:,}")

st.divider()

# ── City coverage map ─────────────────────────────────────────────────────────
col_map, col_table = st.columns([2, 1])

with col_map:
    st.markdown("### Kenya Flood Coverage")
    cities_df = pd.DataFrame(cities)

    # Aggregate per-city incident stats
    if not incidents.empty:
        city_stats = incidents.groupby("city_id").agg(
            total_incidents=("date","count"),
            total_deaths=("deaths","sum"),
            total_displaced=("displaced","sum"),
            enforcement_gap=("policy_enforced", lambda x: (incidents.loc[x.index,"policy_existed"] == True).sum() - (x == True).sum()),
        ).reset_index()
        cities_df = cities_df.merge(city_stats, on="id", how="left").fillna(0)
    else:
        cities_df["total_incidents"] = 0
        cities_df["total_deaths"] = 0
        cities_df["total_displaced"] = 0

    cities_df["size"] = (cities_df["total_displaced"] / 500 + 15).clip(upper=55)
    cities_df["label"] = cities_df["name"] + "<br>" + cities_df["county"]

    fig = go.Figure()
    for tier, t_color, t_label in [(1,"#FF3333","Tier 1 — Critical"), (2,"#FF6B35","Tier 2 — Significant"), (3,"#FFB347","Tier 3 — Notable")]:
        sub = cities_df[cities_df["tier"] == tier]
        fig.add_trace(go.Scattergeo(
            lat=sub["lat"], lon=sub["lon"],
            mode="markers+text",
            name=t_label,
            text=sub["name"],
            textposition="top center",
            textfont=dict(size=10, color="white"),
            marker=dict(
                size=sub["size"],
                color=t_color,
                opacity=0.85,
                line=dict(color="white", width=1),
            ),
            customdata=sub[["county","total_incidents","total_deaths","total_displaced"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>%{customdata[0]}<br>"
                "Incidents: %{customdata[1]:.0f}<br>"
                "Deaths: %{customdata[2]:.0f}<br>"
                "Displaced: %{customdata[3]:,.0f}<extra></extra>"
            ),
        ))
    fig.update_layout(
        geo=dict(
            scope="africa",
            center=dict(lat=-0.5, lon=37.5),
            projection_scale=8,
            showland=True, landcolor="#1A1F2E",
            showocean=True, oceancolor="#0E1117",
            showlakes=True, lakecolor="#1A2A3E",
            showcountries=True, countrycolor="#444",
            showframe=False,
            bgcolor="#0E1117",
        ),
        paper_bgcolor="#0E1117",
        font=dict(color="#E8E8E8"),
        height=500,
        margin=dict(l=0,r=0,t=30,b=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.08,
                    bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("### City Summary")
    if not incidents.empty:
        summary = incidents.groupby("city_name").agg(
            incidents=("date","count"),
            deaths=("deaths","sum"),
            displaced=("displaced","sum"),
        ).sort_values("deaths", ascending=False).reset_index()
        summary.columns = ["City","Incidents","Deaths","Displaced"]
        st.dataframe(summary, use_container_width=True, hide_index=True,
                     column_config={
                         "Displaced": st.column_config.NumberColumn(format="%d"),
                     })
    st.divider()
    st.markdown("**Risk tiers**")
    tier_colors = {1:"#FF3333", 2:"#FF6B35", 3:"#FFB347"}
    tier_labels = {1:"Critical — annual displacement events",
                   2:"Significant — major events most years",
                   3:"Notable — episodic severe flooding"}
    for t in [1,2,3]:
        names = [c["name"] for c in cities if c["tier"] == t]
        st.markdown(
            f'<div style="border-left:3px solid {tier_colors[t]};padding:4px 8px;margin:4px 0;font-size:13px">'
            f'<b style="color:{tier_colors[t]}">T{t}</b> {", ".join(names)}<br>'
            f'<span style="color:#888;font-size:11px">{tier_labels[t]}</span></div>',
            unsafe_allow_html=True
        )

st.divider()

# ── National enforcement gap ──────────────────────────────────────────────────
if not incidents.empty:
    st.markdown("### National Enforcement Gap")
    city_gap = incidents.groupby("city_name").apply(
        lambda df: pd.Series({
            "existed":  int((df["policy_existed"] == True).sum()),
            "enforced": int((df["policy_enforced"] == True).sum()),
            "gap":      int((df["policy_existed"] == True).sum() - (df["policy_enforced"] == True).sum()),
            "incidents": len(df),
        })
    ).reset_index().sort_values("gap", ascending=True)

    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(y=city_gap["city_name"], x=city_gap["enforced"],
                             name="Enforced", orientation="h", marker_color="#4CAF50"))
    fig_gap.add_trace(go.Bar(y=city_gap["city_name"], x=city_gap["gap"],
                             name="Gap (policy existed, not enforced)",
                             orientation="h", marker_color="#FF3333"))
    fig_gap.update_layout(barmode="stack", xaxis_title="Incidents",
                          height=400, showlegend=True)
    st.plotly_chart(dark_layout(fig_gap, "Policy Enforcement Gap by City", 420),
                    use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌊 FloodWatch Kenya")
    st.markdown("**v2.0.0**")
    st.divider()
    st.markdown(f"**{len(cities)} cities** · **{total_incidents} incidents** · **{total_policies} policies**")
    st.divider()
    st.markdown("### Navigate")
    st.markdown("""Use the pages above to explore:
- Incident maps per city
- Policy accountability
- City benchmarks
- Risk calculator
- Community reports""")
    st.divider()
    st.markdown("### Design principle")
    st.markdown("*The enforcement gap is the story. Every feature connects back to the distance between policy existence and implementation.*")
    st.divider()
    st.caption("Part of the [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack) ecosystem")
