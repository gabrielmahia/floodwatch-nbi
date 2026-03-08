"""Page 2 — Impact Analysis: multi-city comparison and per-city deep dive."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_all_incidents, load_incidents, active_cities
from utils.charts import (flood_timeline_chart, zone_impact_bar,
                           enforcement_gap_chart, dark_layout)

st.set_page_config(page_title="Impact Analysis · FloodWatch Kenya", page_icon="📊", layout="wide")
st.markdown("# 📊 Impact Analysis")
st.caption("⚠️ DEMO DATA — representative samples only.")

cities = active_cities()
all_df = load_all_incidents()

mode = st.radio("View", ["National comparison", "Single city deep-dive"], horizontal=True)
st.divider()

if mode == "National comparison":
    if all_df.empty:
        st.warning("No data loaded.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["By City", "Timeline", "Enforcement Gap"])

    with tab1:
        city_agg = all_df.groupby("city_name").agg(
            incidents=("date","count"), deaths=("deaths","sum"),
            displaced=("displaced","sum"),
            damage=("infra_damage_ksh_m","sum"),
            avg_response=("response_days","mean"),
        ).sort_values("deaths", ascending=False).reset_index()

        c1,c2 = st.columns(2)
        with c1:
            fig = px.bar(city_agg.sort_values("deaths",ascending=True),
                         x="deaths", y="city_name", orientation="h",
                         color="deaths", color_continuous_scale=["#1A1F2E","#FF6B35","#FF3333"],
                         text="deaths")
            fig.update_traces(textposition="outside")
            st.plotly_chart(dark_layout(fig,"Deaths by City",420), use_container_width=True)
        with c2:
            fig2 = px.bar(city_agg.sort_values("displaced",ascending=True),
                          x="displaced", y="city_name", orientation="h",
                          color="displaced", color_continuous_scale=["#1A1F2E","#4FC3F7","#1565C0"],
                          text="displaced")
            fig2.update_traces(textposition="outside", texttemplate="%{x:,}")
            st.plotly_chart(dark_layout(fig2,"Displaced by City",420), use_container_width=True)

        st.markdown("### Full comparison table")
        city_agg["avg_response"] = city_agg["avg_response"].round(1)
        city_agg["damage"] = city_agg["damage"].round(1)
        st.dataframe(city_agg.set_index("city_name"), use_container_width=True,
                     column_config={
                         "displaced": st.column_config.NumberColumn(format="%d"),
                         "damage":    st.column_config.NumberColumn("Damage (KSh M)", format="%.1f"),
                     })

    with tab2:
        all_df["year"] = pd.to_datetime(all_df["date"]).dt.year
        yr_city = all_df.groupby(["year","city_name"]).agg(
            deaths=("deaths","sum"), displaced=("displaced","sum")
        ).reset_index()
        fig_t = px.bar(yr_city, x="year", y="displaced", color="city_name",
                       barmode="stack",
                       labels={"displaced":"Displaced","year":"Year","city_name":"City"})
        st.plotly_chart(dark_layout(fig_t,"Annual Displacement by City — All Kenya",440),
                        use_container_width=True)

        fig_t2 = px.line(yr_city.groupby("year")["deaths"].sum().reset_index(),
                          x="year", y="deaths", markers=True,
                          labels={"deaths":"Deaths","year":"Year"})
        fig_t2.update_traces(line_color="#FF3333", marker_color="#FF3333")
        st.plotly_chart(dark_layout(fig_t2,"Annual Deaths — National Total",340),
                        use_container_width=True)

    with tab3:
        city_gap = all_df.groupby("city_name").apply(lambda d: pd.Series({
            "policy_existed":  int((d["policy_existed"]==True).sum()),
            "policy_enforced": int((d["policy_enforced"]==True).sum()),
            "gap": int((d["policy_existed"]==True).sum()-(d["policy_enforced"]==True).sum()),
        })).reset_index().sort_values("gap", ascending=False)

        fig_g = go.Figure()
        fig_g.add_trace(go.Bar(y=city_gap["city_name"], x=city_gap["policy_enforced"],
                               name="Enforced", orientation="h", marker_color="#4CAF50"))
        fig_g.add_trace(go.Bar(y=city_gap["city_name"], x=city_gap["gap"],
                               name="Gap", orientation="h", marker_color="#FF3333"))
        fig_g.update_layout(barmode="stack")
        st.plotly_chart(dark_layout(fig_g,"National Enforcement Gap by City",500),
                        use_container_width=True)

        nat_pct = round(all_df["policy_enforced"].eq(True).sum() /
                        max(all_df["policy_existed"].eq(True).sum(),1) * 100, 1)
        st.metric("National enforcement rate",f"{nat_pct}%",
                  help="% of incidents where relevant policy existed AND was enforced")

else:
    city_name_sel = st.selectbox("Select city",
                                  [c["name"] for c in cities])
    city_meta = next(c for c in cities if c["name"] == city_name_sel)
    df = load_incidents(city_meta["id"])

    if df.empty:
        st.warning(f"No incident data loaded for {city_name_sel}.")
        st.stop()

    st.markdown(f"### {city_name_sel} — {city_meta['county']}")
    st.markdown(f"**Risk type:** {city_meta['risk_type']}  |  "
                f"**Flood season:** {city_meta['flood_season']}")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["Timeline", "Zone Breakdown", "Enforcement Gap"])
    with tab1:
        st.plotly_chart(flood_timeline_chart(df), use_container_width=True)
    with tab2:
        c1,c2 = st.columns(2)
        with c1: st.plotly_chart(zone_impact_bar(df), use_container_width=True)
        with c2:
            cause = df.groupby("cause").agg(incidents=("date","count"),deaths=("deaths","sum")).reset_index()
            fig_c = px.bar(cause, x="cause", y="incidents", color="deaths",
                           color_continuous_scale=["#1A1F2E","#FF6B35","#FF3333"])
            st.plotly_chart(dark_layout(fig_c,"Incidents by Cause",360), use_container_width=True)
    with tab3:
        st.plotly_chart(enforcement_gap_chart(df), use_container_width=True)
        fig_resp = px.box(df, x="severity", y="response_days", color="severity",
                          color_discrete_map={"Critical":"#FF3333","High":"#FF6B35",
                                              "Medium":"#FFB347","Low":"#4CAF50"},
                          category_orders={"severity":["Critical","High","Medium","Low"]})
        st.plotly_chart(dark_layout(fig_resp,"Response Days by Severity",360),
                        use_container_width=True)
