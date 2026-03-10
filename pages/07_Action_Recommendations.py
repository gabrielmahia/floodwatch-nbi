"""
FloodWatch Kenya — Action Recommendations Engine
Translates policy enforcement data into ranked, actionable government briefings.
Organised by intervention type, urgency, and estimated lives saved.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_all_policies, load_all_incidents, load_cities, city_selector
from utils.charts import dark_layout

st.set_page_config(
    page_title="Action Recommendations — FloodWatch Kenya",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@media (max-width: 768px) {
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    [data-testid="stDataFrame"] { overflow-x: auto !important; }
    iframe { width: 100% !important; max-width: 100% !important; }
    .stButton > button { width: 100% !important; min-height: 48px !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Colour palette ────────────────────────────────────────────────────────────
URGENCY_COLORS = {
    "Critical": "#FF3333",
    "High":     "#FF6B35",
    "Medium":   "#FFB347",
    "Low":      "#4CAF50",
}
ACTION_COLORS = {
    "Gazette now":              "#E91E63",
    "Enforce existing order":   "#FF3333",
    "Unblock budget":           "#FF6B35",
    "Resolve coordination gap": "#2196F3",
    "Resolve land dispute":     "#9C27B0",
    "Fix procurement":          "#FF9800",
    "Build capacity":           "#00BCD4",
    "Start implementation":     "#8BC34A",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def classify_blocker(text: str) -> str:
    t = str(text).lower()
    if any(k in t for k in ["gazett", "not adopted", "county assembly", "parliament"]):
        return "gazette"
    if any(k in t for k in ["political", "election", "demolit", "resist"]):
        return "political_will"
    if any(k in t for k in ["budget", "fund", "financ", "diverted", "shortfall"]):
        return "budget"
    if any(k in t for k in ["jurisdict", "cross-county", "inter-agency", "coordination",
                             "upstream", "cross-border", "diplomatic"]):
        return "coordination"
    if any(k in t for k in ["land", "tenure", "resettl", "acquisition"]):
        return "land"
    if any(k in t for k in ["capacity", "staff", "techni", "expertise"]):
        return "capacity"
    if any(k in t for k in ["contract", "procure", "tender", "default"]):
        return "procurement"
    return "other"

BLOCKER_TO_ACTION = {
    "gazette":        ("Gazette now",              "Critical", 1),
    "political_will": ("Enforce existing order",   "High",     2),
    "budget":         ("Unblock budget",           "High",     3),
    "coordination":   ("Resolve coordination gap", "High",     4),
    "land":           ("Resolve land dispute",     "Medium",   5),
    "procurement":    ("Fix procurement",          "Medium",   6),
    "capacity":       ("Build capacity",           "Medium",   7),
    "other":          ("Start implementation",     "Low",      8),
}

STATUS_URGENCY = {
    "Draft Only":             ("Critical", 1),
    "Not Enforced":           ("Critical", 1),
    "Not Started":            ("High",     2),
    "Stalled":                ("High",     2),
    "Partially Implemented":  ("Medium",   3),
    "Completed":              ("Low",      4),
}

RESPONSIBLE_BODY = {
    "gazette":        "County Assembly / Cabinet Secretary",
    "political_will": "County Governor / NEMA",
    "budget":         "National Treasury / County Treasury",
    "coordination":   "Inter-County Technical Committee / Ministry of Interior",
    "land":           "National Land Commission / County Government",
    "procurement":    "County Public Procurement Office",
    "capacity":       "Council of Governors / Ministry of Water",
    "other":          "Implementing Body (per policy)",
}

COST_ESTIMATE = {
    "gazette":        "Zero cost — administrative action only",
    "political_will": "Zero cost — enforcement authority exists",
    "budget":         "Treasury circular required — no new legislation",
    "coordination":   "Inter-county MOU — estimated KSh 2–5M facilitation",
    "land":           "NLC mediation — timeline 6–18 months",
    "procurement":    "Re-tender — 3–6 month process",
    "capacity":       "Training budget — estimated KSh 5–20M",
    "other":          "Varies by policy",
}

TIMELINE = {
    "gazette":        "30–90 days",
    "political_will": "Immediate — existing legal mandate",
    "budget":         "1 budget cycle (next financial year)",
    "coordination":   "3–6 months (MOU negotiation)",
    "land":           "6–24 months",
    "procurement":    "3–6 months",
    "capacity":       "6–12 months",
    "other":          "Varies",
}

@st.cache_data
def get_data():
    policies  = load_all_policies()
    incidents = load_all_incidents()
    cities    = load_cities()
    # Coerce numerics
    for col in ["lives_saved_estimate", "budget_allocated_ksh_m", "budget_utilized_pct"]:
        policies[col] = pd.to_numeric(policies[col], errors="coerce").fillna(0)
    return policies, incidents, cities

def build_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Convert policy rows into ranked recommendations."""
    active = df[df["status"] != "Completed"].copy()
    if active.empty:
        return pd.DataFrame()

    rows = []
    for _, row in active.iterrows():
        blocker_type = classify_blocker(row.get("blocking_factor", ""))
        action_label, urgency_override, sort_order = BLOCKER_TO_ACTION[blocker_type]
        status_urgency, status_sort = STATUS_URGENCY.get(row["status"], ("Medium", 3))

        # Urgency: take the higher of blocker and status signals
        urgency_rank = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        final_urgency = urgency_override if urgency_rank[urgency_override] <= urgency_rank[status_urgency] else status_urgency

        budget_unspent = row["budget_allocated_ksh_m"] * (1 - row["budget_utilized_pct"] / 100)

        rows.append({
            "city_name":        row.get("city_name", ""),
            "policy_name":      row["name"],
            "status":           row["status"],
            "action":           action_label,
            "urgency":          final_urgency,
            "urgency_sort":     urgency_rank[final_urgency],
            "blocker_type":     blocker_type,
            "blocking_factor":  str(row.get("blocking_factor", "")),
            "lives_at_risk":    int(row["lives_saved_estimate"]),
            "budget_unspent_m": round(budget_unspent, 1),
            "responsible_body": RESPONSIBLE_BODY[blocker_type],
            "cost_to_act":      COST_ESTIMATE[blocker_type],
            "timeline":         TIMELINE[blocker_type],
            "implementing_body": row.get("implementing_body", ""),
            "notes":            str(row.get("notes", "")),
        })

    recs = pd.DataFrame(rows)
    # Sort: urgency first, then lives at risk
    recs = recs.sort_values(["urgency_sort", "lives_at_risk"], ascending=[True, False]).reset_index(drop=True)
    recs.index = recs.index + 1
    return recs

# ── Load ──────────────────────────────────────────────────────────────────────
policies, incidents, cities = get_data()

# Attach city_name to policies if not present
if "city_name" not in policies.columns:
    city_map = {c["id"]: c["name"] for c in cities}
    policies["city_name"] = policies["city_id"].map(city_map)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/clipboard-emoji.png", width=48)
    st.markdown("### Recommendations Engine")
    st.markdown(
        "Ranked action briefs for county governments, "
        "the National Treasury, and implementing agencies."
    )
    st.divider()

    view = st.radio("Scope", ["National", "Single city"], horizontal=True)
    if view == "Single city":
        selected = city_selector("Select city", include_all=False)
    else:
        selected = None

    st.divider()
    action_filter = st.multiselect(
        "Filter by action type",
        options=list(ACTION_COLORS.keys()),
        default=list(ACTION_COLORS.keys()),
    )
    urgency_filter = st.multiselect(
        "Filter by urgency",
        options=["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium"],
    )
    st.divider()
    st.caption("Sources: NCC · NEMA · NDMA · WRMA · County CIDP documentation · World Bank project reports")

# ── Filter data ───────────────────────────────────────────────────────────────
if selected:
    df_filtered = policies[policies["city_id"] == selected].copy()
    scope_label = next((c["name"] for c in cities if c["id"] == selected), selected.title())
else:
    df_filtered = policies.copy()
    scope_label = "Kenya — All 25 Cities"

recs = build_recommendations(df_filtered)

if not recs.empty:
    recs = recs[
        recs["action"].isin(action_filter) &
        recs["urgency"].isin(urgency_filter)
    ]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📋 Action Recommendations")
st.markdown(f"**{scope_label}** · Ranked by urgency and lives at risk")
st.divider()

if recs.empty:
    st.info("No recommendations match the current filters.")
    st.stop()

# ── KPI strip ─────────────────────────────────────────────────────────────────
total_lives  = recs["lives_at_risk"].sum()
total_budget = recs["budget_unspent_m"].sum()
critical_n   = len(recs[recs["urgency"] == "Critical"])
zero_cost_n  = len(recs[recs["cost_to_act"].str.startswith("Zero")])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Actions identified", len(recs))
k2.metric("Lives at risk if unresolved", f"{total_lives:,}")
k3.metric("KSh unspent / diverted", f"{total_budget:,.0f}M")
k4.metric("Zero-cost actions", zero_cost_n, help="Actions requiring no new budget — only political or administrative will")
st.divider()

# ── Summary charts ────────────────────────────────────────────────────────────
tab_overview, tab_urgency, tab_actions, tab_full = st.tabs([
    "📊 Overview", "🔴 Critical actions", "🔧 By action type", "📄 Full brief"
])

with tab_overview:
    c1, c2 = st.columns(2)

    with c1:
        # Lives at risk by action type
        agg = recs.groupby("action")["lives_at_risk"].sum().reset_index()
        agg = agg.sort_values("lives_at_risk", ascending=True)
        agg["color"] = agg["action"].map(ACTION_COLORS)
        fig = px.bar(
            agg, x="lives_at_risk", y="action", orientation="h",
            color="action",
            color_discrete_map=ACTION_COLORS,
            labels={"lives_at_risk": "Lives at risk if unresolved", "action": ""},
            text="lives_at_risk",
        )
        fig.update_traces(textposition="outside", textfont_color="#FFFFFF")
        fig.update_layout(showlegend=False)
        st.plotly_chart(dark_layout(fig, "Lives at Risk by Intervention Type", 380),
                        use_container_width=True)

    with c2:
        # Unspent budget by city (top 12)
        city_budget = (recs.groupby("city_name")["budget_unspent_m"]
                       .sum().reset_index()
                       .sort_values("budget_unspent_m", ascending=False)
                       .head(12))
        fig2 = px.bar(
            city_budget, x="budget_unspent_m", y="city_name", orientation="h",
            color="budget_unspent_m",
            color_continuous_scale=["#1A1F2E", "#FF6B35", "#FF3333"],
            labels={"budget_unspent_m": "KSh M unspent", "city_name": ""},
            text="budget_unspent_m",
        )
        fig2.update_traces(textposition="outside", textfont_color="#FFFFFF",
                           texttemplate="%{text:.0f}M")
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(dark_layout(fig2, "Unspent / Diverted Budget by City (KSh M)", 380),
                        use_container_width=True)

    # Blocker taxonomy donut
    blocker_agg = recs.groupby("blocker_type")["lives_at_risk"].sum().reset_index()
    blocker_agg.columns = ["blocker_type", "lives_at_risk"]
    blocker_labels = {
        "gazette": "Not Gazetted", "political_will": "Political Will",
        "budget": "Budget / Funding", "coordination": "Coordination Gap",
        "land": "Land / Tenure", "procurement": "Procurement",
        "capacity": "Capacity", "other": "Other",
    }
    blocker_agg["label"] = blocker_agg["blocker_type"].map(blocker_labels)
    fig3 = px.pie(
        blocker_agg, values="lives_at_risk", names="label",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig3.update_traces(textinfo="percent+label", textfont_color="#FFFFFF")
    st.plotly_chart(dark_layout(fig3, "What Is Blocking Implementation? (by lives at risk)", 360),
                    use_container_width=True)

with tab_urgency:
    st.markdown("### Critical and High priority actions")
    st.caption("Policies where delay directly costs lives — zero-cost and low-cost actions appear first.")

    urgent = recs[recs["urgency"].isin(["Critical", "High"])].copy()
    if urgent.empty:
        st.info("No critical/high urgency actions in current filter.")
    else:
        for _, row in urgent.iterrows():
            urgency_color = URGENCY_COLORS[row["urgency"]]
            with st.expander(
                f"{'🔴' if row['urgency']=='Critical' else '🟠'} "
                f"**{row['action']}** — {row['policy_name']} · {row['city_name']}",
                expanded=False,
            ):
                col1, col2, col3 = st.columns(3)
                col1.metric("Urgency", row["urgency"])
                col2.metric("Lives at risk", f"{row['lives_at_risk']:,}")
                col3.metric("Budget unspent", f"KSh {row['budget_unspent_m']:.0f}M")

                st.markdown(f"**Current status:** `{row['status']}`")
                st.markdown(f"**What is blocking it:** {row['blocking_factor']}")
                st.markdown(f"**Who must act:** {row['responsible_body']}")
                st.markdown(f"**Cost to act:** {row['cost_to_act']}")
                st.markdown(f"**Realistic timeline:** {row['timeline']}")
                if row["notes"] and row["notes"] != "nan":
                    st.markdown(f"**Context:** {row['notes']}")

with tab_actions:
    st.markdown("### Recommendations grouped by intervention type")

    for action_type in list(ACTION_COLORS.keys()):
        subset = recs[recs["action"] == action_type]
        if subset.empty:
            continue
        lives = subset["lives_at_risk"].sum()
        count = len(subset)
        color = ACTION_COLORS[action_type]

        st.markdown(
            f"<div style='border-left:4px solid {color}; padding-left:12px; margin-bottom:4px;'>"
            f"<strong>{action_type}</strong> &nbsp;·&nbsp; "
            f"{count} {'policy' if count==1 else 'policies'} &nbsp;·&nbsp; "
            f"{lives:,} lives at risk"
            f"</div>",
            unsafe_allow_html=True,
        )

        for _, row in subset.iterrows():
            with st.expander(f"{row['policy_name']} — {row['city_name']}", expanded=False):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Urgency:** {row['urgency']}")
                col1.markdown(f"**Status:** `{row['status']}`")
                col1.markdown(f"**Lives at risk:** {row['lives_at_risk']:,}")
                col2.markdown(f"**Responsible body:** {row['responsible_body']}")
                col2.markdown(f"**Cost to act:** {row['cost_to_act']}")
                col2.markdown(f"**Timeline:** {row['timeline']}")
                st.markdown(f"**Blocker:** {row['blocking_factor']}")
                if row["notes"] and row["notes"] != "nan":
                    st.markdown(f"**Background:** {row['notes']}")
        st.markdown("---")

with tab_full:
    st.markdown("### Full action brief — export-ready")
    st.caption(
        "Ranked by urgency then lives at risk. Suitable for government briefings, "
        "county assembly submissions, and donor reports."
    )

    # Five national priority recommendations as a formatted brief
    if selected is None:
        st.markdown("""
#### National Priority Recommendations

**1. Gazette eight stalled flood management plans (30–90 days, zero cost)**
Eight county and national flood management plans are designed, funded in part, and sitting
at the gazette stage. A single Cabinet directive requiring county assemblies to gazette
approved flood management frameworks within 90 days — with a named accountability officer —
costs nothing and unlocks implementation authority for an **estimated 1,930 lives of
annual risk reduction** *(model projection based on incident death rates in the affected 
counties — not a cited external figure; actual impact depends on enforcement quality)*.

**2. Ring-fence flood infrastructure budgets (next budget cycle)**
County development funds are being used as discretionary pools. Kitale's stormwater budget
was re-allocated to road works two consecutive years. Naivasha's drainage budget was
diverted to Nakuru town in 2021. A National Treasury circular ring-fencing gazetted flood
infrastructure allocations from discretionary re-allocation would protect an estimated
**KSh 2,800M** currently at risk of diversion.

**3. Mandate cross-referencing of flood risk maps in planning approvals (immediate, zero cost)**
NCC's flood risk map has been published since 2020. Planning approvals in flood zones
continue to be issued without mandatory cross-referencing. NEMA and NCC jointly hold
the authority to require this check — no legislation is needed. Estimated impact:
**200+ lives annually** from reduced new exposure in flood-risk zones 
*(indicative projection; based on NCC flood risk map coverage gap extrapolation)*.

**4. Establish a single Inter-County Flood Coordination Authority (3–6 months)**
Budalangi, Kisumu, Naivasha, and Embu all have stalled policies whose primary blocker
is jurisdictional fragmentation. The Inter-County Technical Committee framework exists.
Adding flood management to its mandate — with enforcement powers and a named secretariat —
resolves four major coordination failures simultaneously.

**5. Create a dedicated ASAL Flash Flood Response Framework (6–12 months)**
Wajir, Mandera, Isiolo, and Garissa operate in a policy vacuum. The national framework
assumes urban drainage infrastructure. A separate ASAL response architecture — community
early warning, livestock corridor preservation, mobile response capacity — is needed.
Current gap: **near-zero institutional coverage** for an estimated 2.1M people 
*(ASAL county population totals from KNBS 2019 census)*.
""")
        st.divider()

    # Full ranked table
    display_cols = ["city_name", "policy_name", "status", "action", "urgency",
                    "lives_at_risk", "budget_unspent_m", "responsible_body", "timeline"]
    display_df = recs[display_cols].rename(columns={
        "city_name":        "City",
        "policy_name":      "Policy",
        "status":           "Status",
        "action":           "Required Action",
        "urgency":          "Urgency",
        "lives_at_risk":    "Lives at Risk",
        "budget_unspent_m": "KSh M Unspent",
        "responsible_body": "Responsible Body",
        "timeline":         "Timeline",
    })

    def color_urgency(val):
        colors = {"Critical": "background-color:#3D1515; color:#FF6B6B",
                  "High":     "background-color:#3D2010; color:#FF9B55",
                  "Medium":   "background-color:#3D3010; color:#FFD555",
                  "Low":      "background-color:#103D15; color:#69FF79"}
        return colors.get(val, "")

    styled = display_df.style.applymap(color_urgency, subset=["Urgency"])
    st.dataframe(styled, use_container_width=True, height=600)

    st.download_button(
        "⬇ Download as CSV",
        data=display_df.to_csv(index=False).encode(),
        file_name=f"floodwatch_recommendations_{scope_label.lower().replace(' ','_')}.csv",
        mime="text/csv",
    )
