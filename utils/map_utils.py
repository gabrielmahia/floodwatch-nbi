"""Folium map builders for FloodWatch NBI."""
from __future__ import annotations
import folium
from folium.plugins import HeatMap
import pandas as pd


# ── Geographic constants ──────────────────────────────────────────────────────

NAIROBI_CENTER = [-1.2921, 36.8219]

# Approximate riparian corridors (polylines of key rivers through vulnerable zones)
RIPARIAN_ZONES = {
    "Nairobi River": [
        [-1.2631, 36.7819], [-1.2678, 36.7992], [-1.2714, 36.8156],
        [-1.2745, 36.8312], [-1.2789, 36.8489], [-1.2823, 36.8634],
        [-1.2856, 36.8778],
    ],
    "Mathare River": [
        [-1.2456, 36.8623], [-1.2534, 36.8712], [-1.2601, 36.8801],
        [-1.2638, 36.8889], [-1.2689, 36.8967],
    ],
    "Ngong River": [
        [-1.3156, 36.7534], [-1.3189, 36.7712], [-1.3212, 36.7889],
        [-1.3245, 36.8067], [-1.3267, 36.8245],
    ],
    "Gitathuru River": [
        [-1.2245, 36.8834], [-1.2312, 36.8901], [-1.2389, 36.8967],
        [-1.2445, 36.9034],
    ],
}

# High-risk informal settlement zones (approximate bounding boxes as polygons)
VULNERABLE_ZONES = [
    {"name": "Mathare",  "coords": [[-1.257,-1.271, 36.850, 36.900]],
     "color": "#FF3333",
     "polygon": [[-1.257,36.850],[-1.257,36.900],[-1.271,36.900],[-1.271,36.850]]},
    {"name": "Kibera",   "coords": [[-1.305,-1.320, 36.780, 36.810]],
     "color": "#FF6B35",
     "polygon": [[-1.305,36.780],[-1.305,36.810],[-1.320,36.810],[-1.320,36.780]]},
    {"name": "Mukuru",   "coords": [[-1.300,-1.320, 36.860, 36.895]],
     "color": "#FF6B35",
     "polygon": [[-1.300,36.860],[-1.300,36.895],[-1.320,36.895],[-1.320,36.860]]},
    {"name": "Korogocho","coords": [[-1.225,-1.240, 36.885, 36.905]],
     "color": "#FFB347",
     "polygon": [[-1.225,36.885],[-1.225,36.905],[-1.240,36.905],[-1.240,36.885]]},
]

SEVERITY_ICON_COLORS = {
    "Critical": "red",
    "High":     "orange",
    "Medium":   "beige",
    "Low":      "green",
}


# ── Map builders ──────────────────────────────────────────────────────────────

def _base_map(zoom: int = 12) -> folium.Map:
    return folium.Map(
        location=NAIROBI_CENTER,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )


def _add_riparian_corridors(m: folium.Map) -> None:
    for river_name, coords in RIPARIAN_ZONES.items():
        folium.PolyLine(
            locations=coords,
            color="#4FC3F7",
            weight=3,
            opacity=0.7,
            tooltip=f"{river_name} (riparian corridor)",
            dash_array="8 4",
        ).add_to(m)


def _add_vulnerable_zones(m: folium.Map) -> None:
    for zone in VULNERABLE_ZONES:
        folium.Polygon(
            locations=zone["polygon"],
            color=zone["color"],
            weight=1,
            fill=True,
            fill_color=zone["color"],
            fill_opacity=0.12,
            tooltip=f"{zone['name']} — high-risk zone",
        ).add_to(m)


def build_incident_map(incidents_df: pd.DataFrame) -> folium.Map:
    """Folium dark map with incident markers, river corridors, and zone overlays."""
    m = _base_map()
    _add_riparian_corridors(m)
    _add_vulnerable_zones(m)

    for _, row in incidents_df.iterrows():
        color = SEVERITY_ICON_COLORS.get(row["severity"], "gray")
        enforced_str = "✅ Enforced" if str(row.get("policy_enforced","")).lower() == "true" else "❌ Not enforced"
        existed_str  = "✅ Existed" if str(row.get("policy_existed","")).lower() == "true" else "❌ None"

        popup_html = f"""
        <div style="font-family:sans-serif;min-width:220px;color:#111">
          <b style="font-size:14px">{row["location"]}</b><br>
          <span style="color:#888">{row["date"]} · {row["zone"]}</span><br><hr style="margin:4px 0">
          <b>Severity:</b> {row["severity"]}<br>
          <b>Deaths:</b> {row["deaths"]} · <b>Displaced:</b> {int(row["displaced"]):,}<br>
          <b>Cause:</b> {row["cause"]}<br>
          <b>Damage:</b> KSh {row["infra_damage_ksh_m"]}M<br>
          <b>Response:</b> {row["response_days"]} days<br>
          <hr style="margin:4px 0">
          <b>Policy existed:</b> {existed_str}<br>
          <b>Policy enforced:</b> {enforced_str}
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{row['severity']}: {row['location']} ({row['deaths']} deaths)",
            icon=folium.Icon(color=color, icon="tint", prefix="fa"),
        ).add_to(m)

    return m


def build_risk_heatmap(incidents_df: pd.DataFrame) -> folium.Map:
    """Folium heatmap weighted by deaths and displacement."""
    m = _base_map()
    _add_riparian_corridors(m)

    heat_data = []
    for _, row in incidents_df.iterrows():
        weight = (row["deaths"] * 10 + row["displaced"] / 50)
        heat_data.append([row["lat"], row["lon"], weight])

    HeatMap(
        heat_data,
        radius=25,
        blur=20,
        gradient={0.2: "#4FC3F7", 0.5: "#FF6B35", 0.8: "#FF3333", 1.0: "#FFFFFF"},
        min_opacity=0.4,
    ).add_to(m)

    return m
