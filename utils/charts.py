"""Plotly figures and risk calculator for FloodWatch NBI."""
from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ── Theme helper ──────────────────────────────────────────────────────────────

def dark_layout(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#E8E8E8")),
        paper_bgcolor="#1A1F2E",
        plot_bgcolor="#1A1F2E",
        font=dict(color="#E8E8E8"),
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)")
    return fig


SEVERITY_COLORS = {
    "Critical": "#FF3333",
    "High":     "#FF6B35",
    "Medium":   "#FFB347",
    "Low":      "#4CAF50",
}

STATUS_COLORS = {
    "Completed":              "#4CAF50",
    "Partially Implemented":  "#FFB347",
    "Stalled":                "#FF6B35",
    "Not Enforced":           "#FF3333",
    "Not Started":            "#9E9E9E",
    "Draft Only":             "#607D8B",
}


# ── Risk calculator ───────────────────────────────────────────────────────────

def calculate_risk_score(
    population_density: float,
    drainage_coverage: float,
    distance_from_river_m: float,
    riparian_compliant: bool,
    slope_pct: float,
    soil_permeability: float,
) -> float:
    """Composite flood risk score 0–100.

    Component weights:
        population_density   25% — higher density = more people at risk
        drainage_gap         20% — (100 - drainage_coverage)
        river_proximity      25% — closer = higher risk
        riparian_violation   15% — non-compliant adds fixed risk
        flat_terrain         10% — low slope = water pools
        soil_impermeability   5% — clay soils increase runoff

    Args:
        population_density:    persons/hectare (0–1000)
        drainage_coverage:     % coverage (0–100)
        distance_from_river_m: metres from nearest river/stream (0–2000)
        riparian_compliant:    True = compliant (lower risk)
        slope_pct:             terrain gradient % (0–30)
        soil_permeability:     0.0 = clay (high runoff) to 1.0 = sandy (low runoff)

    Returns:
        float: risk score 0–100
    """
    # Normalise each component to 0–1 (1 = maximum risk)
    density_score   = min(population_density / 500.0, 1.0)
    drainage_score  = max(0.0, (100.0 - drainage_coverage) / 100.0)
    proximity_score = max(0.0, 1.0 - (distance_from_river_m / 500.0))
    riparian_score  = 1.0 if not riparian_compliant else 0.0
    flat_score      = max(0.0, 1.0 - (slope_pct / 10.0))
    soil_score      = 1.0 - soil_permeability

    raw = (
        density_score   * 25
        + drainage_score  * 20
        + proximity_score * 25
        + riparian_score  * 15
        + flat_score      * 10
        + soil_score      *  5
    )
    return round(min(max(raw, 0.0), 100.0), 1)


# ── Chart functions ───────────────────────────────────────────────────────────

def flood_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Scatter: time × displaced, bubble size = deaths, colour = severity."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["size"]  = (df["deaths"] * 8 + 20).clip(upper=120)
    df["severity_color"] = df["severity"].map(SEVERITY_COLORS).fillna("#888")

    fig = go.Figure()
    for severity, color in SEVERITY_COLORS.items():
        sub = df[df["severity"] == severity]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["displaced"],
            mode="markers",
            name=severity,
            marker=dict(size=sub["size"], color=color, opacity=0.8,
                        line=dict(color="white", width=1)),
            customdata=sub[["location", "deaths", "cause", "policy_enforced"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Displaced: %{y:,}<br>"
                "Deaths: %{customdata[1]}<br>"
                "Cause: %{customdata[2]}<br>"
                "Policy enforced: %{customdata[3]}<extra></extra>"
            ),
        ))
    fig.update_layout(xaxis_title="Date", yaxis_title="Persons Displaced")
    return dark_layout(fig, "Flood Incidents — Timeline", 420)


def zone_impact_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: displaced + deaths by zone."""
    g = df.groupby("zone").agg(
        displaced=("displaced", "sum"),
        deaths=("deaths", "sum"),
        incidents=("date", "count"),
    ).sort_values("displaced", ascending=True).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=g["zone"], x=g["displaced"], name="Displaced",
        orientation="h", marker_color="#FF6B35",
        hovertemplate="%{y}<br>Displaced: %{x:,}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=g["zone"], x=g["deaths"] * 50, name="Deaths (×50)",
        orientation="h", marker_color="#FF3333", opacity=0.7,
        hovertemplate="%{y}<br>Deaths: %{x:.0f}<extra></extra>",
    ))
    fig.update_layout(barmode="overlay", xaxis_title="Persons", yaxis_title="")
    return dark_layout(fig, "Impact by Zone", 380)


def enforcement_gap_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: incidents where policy existed vs enforced."""
    total     = len(df)
    existed   = df["policy_existed"].sum()
    enforced  = df["policy_enforced"].sum()
    gap       = existed - enforced

    fig = go.Figure(go.Bar(
        x=["Total Incidents", "Policy Existed", "Policy Enforced", "Enforcement Gap"],
        y=[total, existed, enforced, gap],
        marker_color=["#607D8B", "#FFB347", "#4CAF50", "#FF3333"],
        text=[total, existed, enforced, gap],
        textposition="outside",
    ))
    fig.update_layout(yaxis_title="Incidents", showlegend=False)
    return dark_layout(fig, "The Enforcement Gap", 360)


def policy_status_sunburst(df: pd.DataFrame) -> go.Figure:
    """Donut: policy status distribution."""
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    colors = [STATUS_COLORS.get(s, "#888") for s in counts["status"]]

    fig = go.Figure(go.Pie(
        labels=counts["status"], values=counts["count"],
        hole=0.5, marker_colors=colors,
        textinfo="label+percent",
        hovertemplate="%{label}<br>Count: %{value}<extra></extra>",
    ))
    return dark_layout(fig, "Policy Status Distribution", 380)


def budget_gap_chart(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: allocated vs utilised per policy."""
    df = df.copy()
    df["utilized_ksh_m"] = df["budget_allocated_ksh_m"] * df["budget_utilized_pct"] / 100
    df["unused_ksh_m"]   = df["budget_allocated_ksh_m"] - df["utilized_ksh_m"]
    df = df[df["budget_allocated_ksh_m"] > 0].sort_values("budget_allocated_ksh_m", ascending=False)
    short_names = df["name"].str[:35]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=short_names, x=df["utilized_ksh_m"], name="Utilised",
        orientation="h", marker_color="#4CAF50",
        hovertemplate="%{y}<br>Utilised: KSh %{x:.0f}M<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=short_names, x=df["unused_ksh_m"], name="Unspent",
        orientation="h", marker_color="#FF3333",
        hovertemplate="%{y}<br>Unspent: KSh %{x:.0f}M<extra></extra>",
    ))
    fig.update_layout(barmode="stack", xaxis_title="KSh Millions", yaxis_title="",
                      height=420)
    return dark_layout(fig, "Budget Allocated vs Utilised", 440)


def blocker_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap of blocking factors, sized by lives at risk."""
    df = df[df["status"] != "Completed"].copy()
    short = df["blocking_factor"].str.split(" and ").str[0].str.split(",").str[0].str[:40]
    fig = px.treemap(
        df, path=[short], values="lives_saved_estimate",
        color="lives_saved_estimate",
        color_continuous_scale=[[0, "#1A1F2E"], [0.5, "#FF6B35"], [1, "#FF3333"]],
        hover_data={"name": True, "blocking_factor": True},
    )
    fig.update_traces(textinfo="label+value")
    return dark_layout(fig, "Blocking Factors — Lives at Risk (by estimated lives saved if resolved)", 400)


def resilience_radar(cities: list[dict]) -> go.Figure:
    """Polar radar comparing resilience dimensions across cities."""
    dimensions = [
        ("riparian_compliance_pct", "Riparian
Compliance"),
        ("drainage_coverage_pct",   "Drainage
Coverage"),
        ("early_warning_hours",     "Early
Warning"),
        ("flood_budget_usd_per_capita", "Flood Budget
(USD/capita)"),
        ("resilience_score",        "Overall
Resilience"),
    ]
    # Normalise each dimension to 0–100
    max_vals = {
        "riparian_compliance_pct":     100,
        "drainage_coverage_pct":       100,
        "early_warning_hours":         72,
        "flood_budget_usd_per_capita": 320,
        "resilience_score":            100,
    }
    labels = [d[1] for d in dimensions]

    fig = go.Figure()
    for city in cities:
        values = [
            min(city.get(d[0], 0) / max_vals[d[0]] * 100, 100)
            for d in dimensions
        ]
        values.append(values[0])  # close the polygon
        fig.add_trace(go.Scatterpolar(
            r=values, theta=labels + [labels[0]],
            fill="toself", name=city["name"],
            line=dict(color=city.get("color", "#888")),
            fillcolor=city.get("color", "#888"),
            opacity=0.25,
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1A1F2E",
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color="#888"), gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(tickfont=dict(color="#E8E8E8"), gridcolor="rgba(255,255,255,0.1)"),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return dark_layout(fig, "Resilience Dimensions — City Comparison", 500)


def deaths_per_event_scatter(cities: list[dict]) -> go.Figure:
    """Scatter: resilience score vs deaths per event."""
    df = pd.DataFrame(cities)
    fig = px.scatter(
        df, x="resilience_score", y="deaths_per_event_avg",
        size="flood_budget_usd_per_capita",
        color="name", color_discrete_map={c["name"]: c["color"] for c in cities},
        text="name",
        size_max=45,
        hover_data=["country", "population_m", "key_intervention"],
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(showlegend=False,
                      xaxis_title="Resilience Score (0–100)",
                      yaxis_title="Deaths per Flood Event (avg)")
    return dark_layout(fig, "Resilience Score vs Deaths per Event (bubble = flood budget/capita)", 460)
