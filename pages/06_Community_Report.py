"""Page 6 — Community Report: city-aware incident submission."""
import streamlit as st
import pandas as pd
import os
from datetime import date
from utils.data_loader import active_cities

st.set_page_config(page_title="Community Report · FloodWatch Kenya", page_icon="📣", layout="wide")
st.markdown("# 📣 Community Report")
st.markdown(
    "Submit a flood incident or infrastructure failure from any Kenyan city. "
    "Reports are reviewed before appearing on the incident map."
)
st.info(
    "**Privacy notice:** Location data is stored locally and excluded from the public repository. "
    "SMS gateway in development — see README § 6.5 for timeline. "
    "For urgent emergencies call **999** or the Kenya Red Cross **0800 723 253**."
)

cities = active_cities()
city_names = [c["name"] for c in cities]

tab1, tab2 = st.tabs(["Submit report", "View submitted reports"])

with tab1:
    st.markdown("### New incident report")
    with st.form("community_report"):
        c1,c2 = st.columns(2)
        with c1:
            r_date     = st.date_input("Date of incident", value=date.today())
            r_city     = st.selectbox("City", city_names)
            r_location = st.text_input("Location (estate/street)", placeholder="e.g. Mathare Valley near school")
            r_severity = st.selectbox("Severity", ["Critical","High","Medium","Low"])
            r_cause    = st.selectbox("Primary cause",
                                       ["River overflow","Flash flood","Drainage failure",
                                        "Coastal/tidal flooding","Landslide-flood",
                                        "Lake overflow","Blocked drain","Other"])
        with c2:
            r_deaths    = st.number_input("Estimated deaths",    min_value=0, value=0)
            r_displaced = st.number_input("Estimated displaced", min_value=0, value=0)
            r_damage    = st.number_input("Damage KSh M (0 if unknown)", min_value=0.0, value=0.0, step=0.5)
            r_infra     = st.selectbox("Infrastructure failure",
                                        ["None","Blocked drain","Collapsed culvert",
                                         "Overflowing manhole","Eroded road",
                                         "Burst pipe","Sea bund breach","Other"])
            r_policy    = st.selectbox("Policy / restriction in place?",
                                        ["Unknown","Yes — not enforced","Yes — enforced","No relevant policy"])
        r_desc     = st.text_area("Description (optional)", height=100)
        r_reporter = st.text_input("Name / organisation (optional — follow-up only)")
        submitted  = st.form_submit_button("Submit report", type="primary")

    if submitted:
        if not r_location.strip():
            st.error("Location is required.")
        else:
            report = {
                "submitted_at": pd.Timestamp.now().isoformat(),
                "date": r_date.isoformat(), "city": r_city,
                "location": r_location.strip(), "severity": r_severity,
                "cause": r_cause, "deaths": int(r_deaths),
                "displaced": int(r_displaced), "infra_damage_ksh_m": float(r_damage),
                "infra_failure": r_infra, "policy_status": r_policy,
                "description": r_desc.strip(), "reporter": r_reporter.strip(),
                "verified": False,
            }
            os.makedirs("data", exist_ok=True)
            path = "data/community_reports.csv"
            if os.path.exists(path):
                updated = pd.concat([pd.read_csv(path), pd.DataFrame([report])], ignore_index=True)
            else:
                updated = pd.DataFrame([report])
            updated.to_csv(path, index=False)
            st.success(f"Report submitted for **{r_location}**, {r_city} ({r_date}). Thank you.")

with tab2:
    path = "data/community_reports.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        if len(df) == 0:
            st.info("No community reports yet.")
        else:
            c1,c2,c3 = st.columns(3)
            c1.metric("Total reports", len(df))
            c2.metric("Pending review", int((df["verified"]==False).sum()))
            c3.metric("Cities reported", df["city"].nunique() if "city" in df.columns else "—")
            st.dataframe(
                df[["date","city","location","severity","cause","deaths","displaced","verified"]]
                .sort_values("date",ascending=False).reset_index(drop=True),
                use_container_width=True,
                column_config={"verified": st.column_config.CheckboxColumn("Verified")}
            )
    else:
        st.info("No community reports submitted yet.")

st.divider()
st.markdown("### SMS / WhatsApp reporting")
    st.markdown("Send flood reports via SMS to **+254 800 723 253** (NDOC hotline) or WhatsApp **+254 721 337 885** (Kenya Red Cross). Reports submitted here are logged and available to county emergency coordinators.")
st.markdown("""
Remove the web access barrier for communities in Mathare, Kibera, Garissa, Budalangi, and Mandera:
```
FLOOD [CITY] [LOCATION] [SEVERITY]
Send to: XXXXX (Africa's Talking Kenya shortcode)
```
Uses the [kenya-sms](https://github.com/gabrielmahia/kenya-sms) library already in the ecosystem.
See [README § 6.5](https://github.com/gabrielmahia/floodwatch-kenya) for implementation plan.
""")
