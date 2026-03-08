"""Page 3 — Policy Tracker: multi-city, national policy accountability view."""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_all_policies, load_policies, active_cities
from utils.charts import policy_status_sunburst, budget_gap_chart, blocker_treemap, dark_layout

st.set_page_config(page_title="Policy Tracker · FloodWatch Kenya", page_icon="📋", layout="wide")
st.markdown("# 📋 Policy Tracker")
st.caption("Sources: NCC · NEMA enforcement orders · NDMA contingency plans · county CIDP documentation · World Bank project reports")

cities = active_cities()
all_policies = load_all_policies()

mode = st.radio("View", ["National overview", "Single city"], horizontal=True)
st.divider()

STATUS_COLORS = {
    "Completed":"#4CAF50","Partially Implemented":"#FFB347",
    "Stalled":"#FF6B35","Not Enforced":"#FF3333",
    "Not Started":"#9E9E9E","Draft Only":"#607D8B",
}

if mode == "National overview":
    df = all_policies

    # KPIs
    total       = len(df)
    blocked     = len(df[df["status"].isin(["Stalled","Not Enforced","Not Started","Draft Only"])])
    lives_risk  = int(df[df["status"]!="Completed"]["lives_saved_estimate"].sum())
    budget_alloc = df["budget_allocated_ksh_m"].sum()
    budget_used  = (df["budget_allocated_ksh_m"]*df["budget_utilized_pct"]/100).sum()
    idle_pct     = round((1-budget_used/budget_alloc)*100,1) if budget_alloc else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total policies", total)
    c2.metric("Cities covered", df["city_name"].nunique() if "city_name" in df.columns else "—")
    c3.metric("Not on track", blocked,
              delta=f"{round(blocked/total*100)}%", delta_color="inverse")
    c4.metric("Lives at risk", f"{lives_risk:,}")
    c5.metric("Budget idle", f"{idle_pct}%",
              delta=f"KSh {budget_alloc-budget_used:.0f}M unspent", delta_color="inverse")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Status overview", "Budget analysis",
                                       "Blocker taxonomy", "Policy table"])
    with tab1:
        c1,c2 = st.columns(2)
        with c1:
            st.plotly_chart(policy_status_sunburst(df), use_container_width=True)
        with c2:
            city_status = df[df["status"]!="Completed"].groupby(
                ["city_name","status"]).size().reset_index(name="count")
            fig_cs = px.bar(city_status, x="city_name", y="count", color="status",
                            color_discrete_map=STATUS_COLORS, barmode="stack")
            fig_cs.update_xaxes(tickangle=45)
            st.plotly_chart(dark_layout(fig_cs,"Unresolved Policies by City",420),
                            use_container_width=True)

    with tab2:
        st.plotly_chart(budget_gap_chart(df), use_container_width=True)
        # Per-city budget absorption
        city_budget = df.groupby("city_name").apply(lambda d: pd.Series({
            "allocated": d["budget_allocated_ksh_m"].sum(),
            "utilized":  (d["budget_allocated_ksh_m"]*d["budget_utilized_pct"]/100).sum(),
        })).reset_index()
        city_budget["idle_pct"] = (
            (city_budget["allocated"]-city_budget["utilized"]) /
            city_budget["allocated"].replace(0,1) * 100
        ).round(1)
        city_budget = city_budget.sort_values("idle_pct", ascending=False)
        fig_cb = px.bar(city_budget, x="city_name", y="idle_pct",
                        color="idle_pct",
                        color_continuous_scale=["#4CAF50","#FF6B35","#FF3333"],
                        labels={"idle_pct":"Budget idle %","city_name":"City"})
        fig_cb.update_xaxes(tickangle=45)
        st.plotly_chart(dark_layout(fig_cb,"Budget Idle % by City",380),
                        use_container_width=True)

    with tab3:
        st.plotly_chart(blocker_treemap(df), use_container_width=True)
        # Cross-cutting blockers
        blocker_df = df[df["status"]!="Completed"].copy()
        blocker_df["blocker_short"] = (blocker_df["blocking_factor"]
                                       .str.split(" and ").str[0]
                                       .str.split(",").str[0]
                                       .str[:50])
        blocker_summary = (blocker_df.groupby("blocker_short")
                           .agg(policies=("policy_id","count"),
                                cities=("city_name","nunique"),
                                lives_at_risk=("lives_saved_estimate","sum"))
                           .sort_values("lives_at_risk",ascending=False)
                           .reset_index())
        st.markdown("**Top blocking factors — national**")
        st.dataframe(blocker_summary.head(15), use_container_width=True,
                     column_config={"lives_at_risk":
                         st.column_config.NumberColumn("Lives at risk",format="%d")})

    with tab4:
        city_filter = st.multiselect("Filter by city",
                                      sorted(df["city_name"].unique()),
                                      default=sorted(df["city_name"].unique()))
        status_filter = st.multiselect("Filter by status",
                                        sorted(df["status"].unique()),
                                        default=sorted(df["status"].unique()))
        view_df = df[df["city_name"].isin(city_filter) & df["status"].isin(status_filter)]
        st.dataframe(view_df[["city_name","policy_id","name","status","implementing_body",
                               "budget_allocated_ksh_m","budget_utilized_pct",
                               "lives_saved_estimate","blocking_factor"
                              ]].reset_index(drop=True),
                     use_container_width=True,
                     column_config={
                         "budget_allocated_ksh_m": st.column_config.NumberColumn("Budget (KSh M)",format="%.0f"),
                         "budget_utilized_pct": st.column_config.ProgressColumn("Utilised %",min_value=0,max_value=100),
                         "lives_saved_estimate": st.column_config.NumberColumn("Lives at risk",format="%d"),
                     })

else:  # Single city
    city_sel = st.selectbox("Select city", [c["name"] for c in cities])
    city_meta = next(c for c in cities if c["name"] == city_sel)
    df = load_policies(city_meta["id"])

    if df.empty:
        st.warning(f"No policy data for {city_sel}.")
        st.stop()

    lives_risk  = int(df[df["status"]!="Completed"]["lives_saved_estimate"].sum())
    budget_alloc = df["budget_allocated_ksh_m"].sum()
    budget_used  = (df["budget_allocated_ksh_m"]*df["budget_utilized_pct"]/100).sum()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Policies tracked", len(df))
    c2.metric("Not on track",
              len(df[df["status"].isin(["Stalled","Not Enforced","Not Started","Draft Only"])]))
    c3.metric("Lives at risk", f"{lives_risk:,}")
    c4.metric("Budget idle", f"KSh {budget_alloc-budget_used:.0f}M")
    st.divider()

    c1,c2 = st.columns(2)
    with c1: st.plotly_chart(policy_status_sunburst(df), use_container_width=True)
    with c2: st.plotly_chart(budget_gap_chart(df), use_container_width=True)
    st.plotly_chart(blocker_treemap(df), use_container_width=True)

    selected_id = st.selectbox("View policy detail", df["policy_id"].tolist())
    if selected_id:
        row = df[df["policy_id"]==selected_id].iloc[0]
        color = STATUS_COLORS.get(row["status"],"#888")
        st.markdown(f"""
        <div style="background:#1A1F2E;border-left:4px solid {color};padding:16px;border-radius:4px">
          <h4 style="margin:0 0 8px 0">{row["name"]}</h4>
          <p><b>Status:</b> <span style="color:{color}">{row["status"]}</span> | <b>{row["implementing_body"]}</b> | since {row["year_recommended"]}</p>
          <p><b>Budget:</b> KSh {row["budget_allocated_ksh_m"]:.0f}M · {row["budget_utilized_pct"]:.0f}% utilised</p>
          <p><b>Primary blocker:</b> {row["blocking_factor"]}</p>
          <p><b>Lives at risk if unresolved:</b> {int(row["lives_saved_estimate"]):,}</p>
          <p style="color:#ccc">{row["notes"]}</p>
        </div>
        """, unsafe_allow_html=True)
