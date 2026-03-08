"""FloodWatch NBI - test suite."""
from __future__ import annotations
import json
import pandas as pd
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.charts import calculate_risk_score

ROOT = Path(__file__).parent.parent


class TestRiskScore:
    def test_score_always_in_bounds(self):
        for args in [
            (500, 0, 0, True, 0, 0.0),
            (0, 100, 1000, False, 30, 1.0),
            (250, 50, 250, True, 5, 0.5),
        ]:
            score = calculate_risk_score(*args)
            assert 0 <= score <= 100, f"Score {score} out of bounds for args {args}"

    def test_critical_risk(self):
        # Max density, no drainage, on river, riparian violation, flat, clay
        score = calculate_risk_score(500, 0, 0, True, 0, 0.0)
        assert score >= 70, f"Expected critical score >= 70, got {score}"

    def test_low_risk(self):
        # Low density, full drainage, far from river, compliant, steep, sandy
        score = calculate_risk_score(5, 100, 1000, False, 20, 1.0)
        assert score < 15, f"Expected low score < 15, got {score}"

    def test_riparian_violation_adds_penalty(self):
        base  = calculate_risk_score(100, 50, 200, False, 5, 0.3)
        viol  = calculate_risk_score(100, 50, 200, True,  5, 0.3)
        assert viol > base, "Riparian violation should increase risk score"

    def test_closer_river_higher_risk(self):
        near = calculate_risk_score(100, 50, 10, False, 5, 0.3)
        far  = calculate_risk_score(100, 50, 900, False, 5, 0.3)
        assert near > far, "Closer to river should have higher risk"

    def test_better_drainage_lower_risk(self):
        poor = calculate_risk_score(100, 10, 200, False, 5, 0.3)
        good = calculate_risk_score(100, 90, 200, False, 5, 0.3)
        assert poor > good, "Better drainage should lower risk"

    def test_score_is_float(self):
        score = calculate_risk_score(100, 50, 200, False, 5, 0.5)
        assert isinstance(score, float)

    def test_zero_density_reduces_score(self):
        high = calculate_risk_score(500, 50, 200, False, 5, 0.5)
        zero = calculate_risk_score(0,   50, 200, False, 5, 0.5)
        assert zero < high


class TestDataFiles:
    def test_incidents_loads(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        assert len(df) > 0
        assert "deaths" in df.columns
        assert "policy_existed" in df.columns
        assert "policy_enforced" in df.columns

    def test_incidents_has_required_columns(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        required = ["date", "location", "zone", "lat", "lon", "severity",
                    "deaths", "displaced", "cause", "policy_existed", "policy_enforced"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_incidents_coords_in_nairobi(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        # Nairobi bounding box (roughly)
        assert df["lat"].between(-1.45, -1.15).all(), "Lat values outside Nairobi bounds"
        assert df["lon"].between(36.65, 37.05).all(), "Lon values outside Nairobi bounds"

    def test_severity_values_valid(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        valid = {"Critical", "High", "Medium", "Low"}
        invalid = set(df["severity"].unique()) - valid
        assert not invalid, f"Invalid severity values: {invalid}"

    def test_deaths_non_negative(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        assert (df["deaths"] >= 0).all()

    def test_displaced_non_negative(self):
        df = pd.read_csv(ROOT / "data" / "incidents.csv")
        assert (df["displaced"] >= 0).all()

    def test_policies_loads(self):
        df = pd.read_csv(ROOT / "data" / "policies.csv")
        assert len(df) == 10

    def test_policies_ids_unique(self):
        df = pd.read_csv(ROOT / "data" / "policies.csv")
        assert df["policy_id"].nunique() == len(df)

    def test_budget_utilisation_in_range(self):
        df = pd.read_csv(ROOT / "data" / "policies.csv")
        assert (df["budget_utilized_pct"] >= 0).all()
        assert (df["budget_utilized_pct"] <= 100).all()

    def test_benchmarks_loads(self):
        with open(ROOT / "data" / "city_benchmarks.json") as f:
            data = json.load(f)
        assert "cities" in data
        assert len(data["cities"]) == 6

    def test_benchmarks_nairobi_present(self):
        with open(ROOT / "data" / "city_benchmarks.json") as f:
            data = json.load(f)
        names = [c["name"] for c in data["cities"]]
        assert "Nairobi" in names

    def test_benchmarks_resilience_scores_in_range(self):
        with open(ROOT / "data" / "city_benchmarks.json") as f:
            data = json.load(f)
        for city in data["cities"]:
            assert 0 <= city["resilience_score"] <= 100, (
                f"{city['name']} resilience_score out of range"
            )

    def test_nairobi_lower_resilience_than_rotterdam(self):
        with open(ROOT / "data" / "city_benchmarks.json") as f:
            data = json.load(f)
        by_name = {c["name"]: c for c in data["cities"]}
        assert by_name["Nairobi"]["resilience_score"] < by_name["Rotterdam"]["resilience_score"]
