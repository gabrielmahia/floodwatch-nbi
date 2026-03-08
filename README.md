# FloodWatch NBI

**Urban flood resilience intelligence for Nairobi** — incident tracking, policy accountability, city benchmarking.

[![CI](https://github.com/gabrielmahia/floodwatch-nbi/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielmahia/floodwatch-nbi/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![Tests](https://img.shields.io/badge/tests-20%20passing-brightgreen)](#)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](#)

> DEMO DATA - All incident figures are illustrative samples.
> Real data: NCC incident reports, NDOC, Kenya Red Cross.

Nairobi floods repeatedly. The policy instruments to address this largely exist.
The problem is an **enforcement and accountability gap**, not a knowledge gap.
This platform makes that gap visible and measurable.

---

## Quick start

```bash
git clone https://github.com/gabrielmahia/floodwatch-nbi
cd floodwatch-nbi
pip install -r requirements.txt
streamlit run app.py
```

App runs at `http://localhost:8501`.

---

## Pages

| Page | What it shows |
|------|--------------|
| Landing (`app.py`) | KPI summary, enforcement gap headline, active alert banner |
| 01 Incident Map | Folium dark map, severity/zone/cause filters, heatmap toggle, incident log |
| 02 Impact Analysis | Zone breakdowns, seasonality, cause treemap, enforcement gap detail |
| 03 Policy Tracker | 10 policies: status donut, budget gap, blocker taxonomy, lives at risk |
| 04 City Benchmarks | Radar + scatter: Nairobi vs Rotterdam, Medellin, Dhaka, Singapore, Jakarta |
| 05 Risk Calculator | Site-level composite risk score with component breakdown |
| 06 Community Report | Citizen incident submission form (stores to CSV, pending admin review) |

---

## The enforcement gap

The central insight: in the sampled incidents, a relevant flood policy existed but was
not being enforced in the majority of cases. This is not a data problem or a technical
problem. It is a political economy problem — which is why this platform tracks
*who failed to act* and *what blocked them*, not just *where water went*.

---

## Data schemas

See [HANDOFF.md](HANDOFF.md) for full column-level documentation of:
- `data/incidents.csv` — 12 columns including `policy_existed` / `policy_enforced` pair
- `data/policies.csv` — 10 policies with blocking factor taxonomy
- `data/city_benchmarks.json` — 6-city resilience comparison dataset

---

## Extension roadmap

Priority order by impact-to-effort:

1. **Real-time rainfall** — KMD API or OpenWeatherMap alert banner
2. **WRMA river gauge alerts** — Mathare, Nairobi, Ngong, Athi thresholds
3. **Ward-level choropleth** — 85 Nairobi wards mapped to sitting MCAs
4. **Community report -> map pipeline** — close the submission-to-map loop
5. **SMS gateway** — Africa's Talking inbound: `FLOOD [LOCATION] [SEVERITY]`
6. **Policy changelog + email alerts** — SendGrid notifications on status regression
7. **Developer impact assessment** — flag approved developments against risk scores

Full implementation notes in [HANDOFF.md](HANDOFF.md).

---

## Design principles

**The enforcement gap is the story.** Every feature should connect back to the
distance between policy existence and implementation.

**Name the blockers, not just the outcomes.** Which actors, which decisions.

**Community data supplements but does not replace structural analysis.**

**The city comparison is diagnostic, not aspirational.** Rotterdam is the ceiling.
Medellin is the relevant analogue. Dhaka is the warning.

---

## Stack

- Python 3.11+
- Streamlit 1.32+
- Plotly 5.18+
- Folium 0.15+
- streamlit-folium 0.18+
- Pandas 2.0+

---

*Part of the [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack) East Africa engineering ecosystem.*
*Maintained by [Gabriel Mahia](https://github.com/gabrielmahia). Kenya x USA.*
