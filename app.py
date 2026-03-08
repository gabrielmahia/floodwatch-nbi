"""
FloodWatch Kenya — Urban flood resilience intelligence across Kenya.

Architecture: city-config driven. Each city has its own flood typology,
data files, and institutional accountability context.
Active: Nairobi. Coming soon: Kisumu, Mombasa, Nakuru, Garissa.

⚠️  DEMO DATA — Nairobi incident and policy records are representative samples.
    See sidebar for data sources and § 12 of README.
"""
import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="FloodWatch Kenya",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── City registry ──────────────────────────────────────────────────────────────
@st.cache_data
def load_cities():
    with open("data/cities.json") as f:
        return json.load(f)["cities"]

@st.cache_data
def load_incidents():
    return pd.read_csv("data/incidents.csv")

@st.cache_data
def load_policies():
    return pd.read_csv("data/policies.csv")

cities     = load_cities()
active     = [c for c in cities if c["data_available"]]
coming     = [c for c in cities if not c["data_available"]]
city       = active[0]   # Nairobi — only active city

incidents  = load_incidents()
policies   = load_policies()

# ── Alert banner ──────────────────────────────────────────────────────────────
# Replace with live KMD API call — see README § 6.1
ALERT_ACTIVE  = True
ALERT_LEVEL   = "HIGH"
ALERT_MESSAGE = (
    "Long-rains season active (April–June). Mathare and Mukuru on elevated watch. "
    "Drainage clearance incomplete in 7 sub-wards. "
    "Kisumu: Lake Victoria gauge at 84% of flood stage."
)
if ALERT_ACTIVE:
    color = {"HIGH": "#FF6B35", "CRITICAL": "#FF3333", "WATCH": "#FFB347"}.get(ALERT_LEVEL, "#FF6B35")
    st.markdown(
        f'''<div style="background:{color}22;border-left:4px solid {color};padding:12px 16px;
                border-radius:4px;margin-bottom:16px;">
          <span style="color:{color};font-weight:700">⚠ FLOOD ALERT — {ALERT_LEVEL}</span>
          <span style="color:#E8E8E8;margin-left:12px">{ALERT_MESSAGE}</span>
        </div>''', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🌊 FloodWatch Kenya")
st.markdown(
    "Flood resilience intelligence across Kenya. "
    "Tracking incidents, policy accountability, and the enforcement gap — city by city."
)
st.markdown(
    "<small style='color:#888'>⚠️ DEMO DATA · Nairobi active · "
    "Kisumu / Mombasa / Nakuru / Garissa datasets in development</small>",
    unsafe_allow_html=True,
)
st.divider()

# ── City status map ───────────────────────────────────────────────────────────
st.markdown("### Cities")
cols = st.columns(len(cities))
for i, c in enumerate(cities):
    with cols[i]:
        if c["data_available"]:
            badge = f'''<div style="background:{c["colour"]}22;border:1px solid {c["colour"]};
                border-radius:6px;padding:12px;text-align:center">
                <div style="font-size:18px;font-weight:700;color:{c["colour"]}">{c["name"]}</div>
                <div style="font-size:11px;color:#4CAF50;margin-top:4px">● LIVE</div>
                <div style="font-size:11px;color:#888;margin-top:2px">{c["typology_label"][:30]}...</div>
            </div>'''
        else:
            badge = f'''<div style="background:#1A1F2E;border:1px solid #333;
                border-radius:6px;padding:12px;text-align:center;opacity:0.7">
                <div style="font-size:18px;font-weight:700;color:#888">{c["name"]}</div>
                <div style="font-size:11px;color:#607D8B;margin-top:4px">◌ Coming soon</div>
                <div style="font-size:11px;color:#555;margin-top:2px">{c["typology_label"][:30]}...</div>
            </div>'''
        st.markdown(badge, unsafe_allow_html=True)

st.divider()

# ── Nairobi KPIs ──────────────────────────────────────────────────────────────
st.markdown(f"### {city['name']} — Active dataset")
st.caption(f"Flood typology: **{city['typology_label']}** · Peak season: {city['season_peak']}")

total_deaths    = int(incidents["deaths"].sum())
total_displaced = int(incidents["displaced"].sum())
critical_count  = len(incidents[incidents["severity"] == "Critical"])
policy_gap      = int(incidents["policy_existed"].sum()) - int(incidents["policy_enforced"].sum())
avg_response    = incidents["response_days"].mean()
lives_at_risk   = policies[policies["status"] != "Completed"]["lives_saved_estimate"].sum()
budget_alloc    = policies["budget_allocated_ksh_m"].sum()
budget_used     = (policies["budget_allocated_ksh_m"] * policies["budget_utilized_pct"] / 100).sum()
budget_idle_pct = round((1 - budget_used / budget_alloc) * 100, 1)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💀 Deaths (sample)", f"{total_deaths:,}")
c2.metric("🏠 Displaced (sample)", f"{total_displaced:,}")
c3.metric("⚡ Critical incidents", critical_count)
c4.metric("❌ Enforcement gap", policy_gap,
          help="Incidents where relevant policy existed but was not enforced")
c5.metric("⏱ Avg response", f"{avg_response:.1f} days")

st.divider()
c6, c7, c8 = st.columns(3)
c6.metric("🚫 Policies stalled / not enforced",
          len(policies[policies["status"].isin(["Stalled","Not Enforced","Not Started","Draft Only"])]),
          delta=f"of {len(policies)} tracked", delta_color="inverse")
c7.metric("❤ Lives at risk (policy gap)", f"{lives_at_risk:,}",
          help="Estimated lives saved if stalled policies were fully implemented")
c8.metric("💰 Budget idle", f"{budget_idle_pct}%",
          delta=f"KSh {budget_alloc-budget_used:.0f}M unspent", delta_color="inverse")

st.divider()

# ── Flood typology explainer ───────────────────────────────────────────────────
st.markdown("### Kenya flood typology map")
st.markdown("Each city faces a structurally different flood problem requiring a different response.")

typology_rows = [
    ("🟠 Nairobi",  "Urban drainage",    "Enforcement gap — riparian land has commercial value, NCC avoids pre-election evictions",           "active"),
    ("🔵 Kisumu",   "Lake basin rise",   "Monitoring gap — early warning must track Lake Victoria gauge, not local rainfall",                  "soon"),
    ("🟢 Mombasa",  "Coastal/storm surge","Climate gap — sea level rise trajectory makes parts of Mombasa Island permanently uninsurable by 2060", "soon"),
    ("🟡 Nakuru",   "Endorheic lake",    "Policy gap — no managed retreat framework exists. Conventional flood management does not apply",     "soon"),
    ("🟣 Garissa",  "Riverine/pastoral", "Last-mile gap — early warning exists but cannot reach dispersed pastoral communities",              "soon"),
]
for city_label, typology, gap, status in typology_rows:
    badge = "🟢 LIVE" if status == "active" else "⚪ Coming soon"
    st.markdown(
        f"**{city_label}** &nbsp;·&nbsp; _{typology}_ &nbsp;·&nbsp; {gap} &nbsp;&nbsp; `{badge}`"
    )

st.divider()

# ── Navigation ─────────────────────────────────────────────────────────────────
st.markdown("### Nairobi — explore the data")
r1c1, r1c2, r1c3 = st.columns(3)
with r1c1: st.info("📍 **Incident Map**

Interactive dark map — severity markers, river corridors, risk heatmap.")
with r1c2: st.info("📊 **Impact Analysis**

Zone breakdowns, seasonality, enforcement gap quantified.")
with r1c3: st.info("📋 **Policy Tracker**

Budget utilisation, blocking factors, lives at risk from stalled policies.")
r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: st.info("🌍 **City Benchmarks**

Nairobi vs Medellin, Rotterdam, Jakarta, Dhaka, Singapore.")
with r2c2: st.info("🔧 **Risk Calculator**

Site-level composite flood risk score — any location in Nairobi.")
with r2c3: st.info("📣 **Community Report**

Submit an incident from the field. SMS gateway coming.")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌊 FloodWatch Kenya")
    st.markdown("**v0.2.0 · DEMO DATA**")
    st.divider()
    st.markdown("### Active cities")
    for c in active:
        st.markdown(f"🟢 **{c['name']}** — {c['typology_label'][:40]}")
    st.markdown("### Coming soon")
    for c in coming:
        st.markdown(f"⚪ {c['name']} — {c['typology_label'][:35]}...")
    st.divider()
    st.markdown("### Design principle")
    st.markdown(
        "*The enforcement gap is the story. Every feature connects back "
        "to the distance between policy existence and implementation.*"
    )
    st.divider()
    st.caption("Part of the [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack)")
    st.caption("[Gabriel Mahia](https://github.com/gabrielmahia) · Kenya × USA")
