"""
FloodWatch NBI — Folium map builders.

All maps use CartoDB dark tiles. Riparian corridors and
vulnerable zone overlays are hardcoded as WGS84 polylines.
Update RIPARIAN_ZONES and VULNERABLE_ZONES when adding new areas.
"""
from __future__ import annotations

import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd

# ── Nairobi geographic constants ─────────────────────────────────
NAIROBI_CENTER = [-1.286389, 36.817223]

# Approximate riparian corridors (WGS84 polylines)
# Source: WRMA / Google Earth approximations — replace with actual WRMA GIS data
RIPARIAN_ZONES = [
    {
        "name": "Nairobi River",
        "color": "#3B82F6",
        "coords": [
            [-1.2750, 36.7650], [-1.2700, 36.7850], [-1.2650, 36.8050],
            [-1.2600, 36.8200], [-1.2620, 36.8400], [-1.2700, 36.8600],
            [-1.2800, 36.8800], [-1.2950, 36.9100],
        ],
    },
    {
        "name": "Mathare River",
        "color": "#60A5FA",
        "coords": [
            [-1.2500, 36.8500], [-1.2550, 36.8650], [-1.2600, 36.8800],
            [-1.2650, 36.9000], [-1.2700, 36.9200],
        ],
    },
    {
        "name": "Ngong River",
        "color": "#93C5FD",
        "coords": [
            [-1.3150, 36.7800], [-1.3100, 36.7950], [-1.3050, 36.8100],
            [-1.3000, 36.8300], [-1.3050, 36.8500],
        ],
    },
    {
        "name": "Gitathuru River",
        "color": "#BFDBFE",
        "coords": [
            [-1.2300, 36.8400], [-1.2400, 36.8500], [-1.2500, 36.8600],
            [-1.2600, 36.8700],
        ],
    },
]

# Known high-vulnerability zones (approximate bounding polygons)
VULNERABLE_ZONES = [
    {
        "name": "Mathare Valley",
        "color": "#EF4444",
        "coords": [
            [-1.2550, 36.8550], [-1.2550, 36.8700],
            [-1.2650, 36.8700], [-1.2650, 36.8550], [-1.2550, 36.8550],
        ],
    },
    {
        "name": "Mukuru Settlements",
        "color": "#F97316",
        "coords": [
            [-1.3050, 36.8700], [-1.3050, 36.8950],
            [-1.3200, 36.8950], [-1.3200, 36.8700], [-1.3050, 36.8700],
        ],
    },
    {
        "name": "Kibera",
        "color": "#EAB308",
        "coords": [
            [-1.3050, 36.7700], [-1.3050, 36.8000],
            [-1.3250, 36.8000], [-1.3250, 36.7700], [-1.3050, 36.7700],
        ],
    },
]

SEVERITY_COLORS = {
    "Critical": "#EF4444",
    "High":     "#F97316",
    "Medium":   "#EAB308",
    "Low":      "#22C55E",
}


def _dark_map(zoom: int = 12) -> folium.Map:
    return folium.Map(
        location=NAIROBI_CENTER,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="© CartoDB © OpenStreetMap contributors",
    )


def _add_riparian_overlays(m: folium.Map) -> None:
    for river in RIPARIAN_ZONES:
        folium.PolyLine(
            locations=river["coords"],
            color=river["color"],
            weight=3,
            opacity=0.7,
            tooltip=f"🌊 {river['name']} corridor",
            popup=folium.Popup(
                f"<b>{river['name']}</b><br>30m riparian reserve required under Water Act 2016",
                max_width=220,
            ),
        ).add_to(m)


def _add_vulnerable_zones(m: folium.Map) -> None:
    for zone in VULNERABLE_ZONES:
        folium.Polygon(
            locations=zone["coords"],
            color=zone["color"],
            fill=True,
            fill_opacity=0.12,
            weight=1.5,
            tooltip=f"⚠ {zone['name']} — high vulnerability zone",
        ).add_to(m)


def build_incident_map(df: pd.DataFrame) -> folium.Map:
    """Dark Folium map with incident markers, riparian corridors, and zone overlays.

    Marker icon colour encodes severity. Popup shows incident detail.
    """
    m = _dark_map()
    _add_riparian_overlays(m)
    _add_vulnerable_zones(m)

    cluster = MarkerCluster(
        options={
            "maxClusterRadius": 40,
            "disableClusteringAtZoom": 14,
        }
    )

    for _, row in df.iterrows():
        color  = SEVERITY_COLORS.get(row["severity"], "#94A3B8")
        icon   = "exclamation-triangle" if row["severity"] in ("Critical", "High") else "info-sign"
        enforced_text = (
            "✓ Enforced" if row["policy_enforced"]
            else ("⚠ NOT enforced" if row["policy_existed"] else "✗ No policy")
        )
        popup_html = f"""
        <div style="font-family:monospace; font-size:12px; min-width:200px;">
            <b style="color:{color}">{row['severity'].upper()}</b> — {row['location']}<br>
            <hr style="border-color:#334155; margin:4px 0">
            <b>Date:</b> {row['date']}<br>
            <b>Cause:</b> {row['cause']}<br>
            <b>Deaths:</b> {row['deaths']} &nbsp; <b>Displaced:</b> {row['displaced']:,}<br>
            <b>Damage:</b> KSh {row['infra_damage_ksh_m']:.0f}M<br>
            <b>Response:</b> {row['response_days']} days<br>
            <b>Policy:</b> {enforced_text}
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row['severity']} — {row['location']} ({row['date']})",
            icon=folium.Icon(color="red" if row["severity"] == "Critical" else
                             "orange" if row["severity"] == "High" else "beige",
                             icon=icon, prefix="glyphicon"),
        ).add_to(cluster)

    cluster.add_to(m)
    folium.LayerControl().add_to(m)
    return m


def build_risk_heatmap(df: pd.DataFrame) -> folium.Map:
    """Heatmap weighted by deaths + displacement."""
    m = _dark_map()
    _add_riparian_overlays(m)

    heat_data = [
        [row["lat"], row["lon"], row["deaths"] * 50 + row["displaced"] * 0.1]
        for _, row in df.iterrows()
    ]
    HeatMap(
        heat_data,
        radius=25,
        blur=18,
        gradient={"0.3": "#3B82F6", "0.6": "#EAB308", "1.0": "#EF4444"},
    ).add_to(m)
    return m
