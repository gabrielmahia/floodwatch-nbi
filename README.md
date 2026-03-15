# 🌊 Mafuriko — Flood Risk Intelligence Kenya

**Urban flood resilience intelligence for Kenya — 25 cities, national enforcement gap tracking.**

[![Live App](https://img.shields.io/badge/Live%20App-floodwatch--kenya.streamlit.app-FF4B4B?logo=streamlit)](https://floodwatch-kenya.streamlit.app)
[![CI](https://github.com/gabrielmahia/floodwatch-kenya/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielmahia/floodwatch-kenya/actions)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey)](LICENSE)

> **Mafuriko** /mɑːfuːɾikɔ/ — *Kiswahili*: floods, inundation.

⚠️ **DEMO DATA** — All records are representative samples. See § Real Data Sources for authoritative datasets.

---

## What this is

Kenya floods every year. The policies to address this largely exist. The problem is an **enforcement and accountability gap** — not a knowledge gap. This platform makes that gap visible, measurable, and politically costly to ignore.

Design principle: *track who failed to act and what blocked them, not just where water went.*

---

## Coverage — 25 cities

### Tier 1 — Critical (annual displacement events)
| City | County | Risk profile |
|------|--------|-------------|
| Nairobi | Nairobi City | Urban drainage failure, riparian encroachment |
| Garissa | Garissa | Tana River overflow — most lethal single-event floods |
| Budalangi | Busia | Nzoia River — most flood-prone constituency in Kenya |
| Kisumu | Kisumu | Lake Victoria backflow + Nyando River compound risk |
| Mombasa | Mombasa | Coastal tidal surge + Tudor Creek overflow |
| Mandera | Mandera | Daua River cross-border (Ethiopia/Somalia) — zero advance warning |

### Tier 2 — Significant (major events most years)
Nakuru · Eldoret · Kericho · Malindi · Thika · Naivasha · Nyeri · Meru

### Tier 3 — Notable (episodic severe flooding)
Homa Bay · Migori · Kitale · Athi River · Embu · Lamu · Voi · Isiolo · Wajir · Machakos · Nanyuki

**Total population covered: ~11M**

---

## Quick start

```bash
git clone https://github.com/gabrielmahia/floodwatch-kenya
cd floodwatch-kenya
pip install -r requirements.txt
streamlit run app.py
```

Deploy: [share.streamlit.io](https://share.streamlit.io) → New app → `app.py`. No secrets needed.

---

## Adding a city (zero code required)

1. Create `data/{city_id}/incidents.csv` — schema: see any existing city
2. Create `data/{city_id}/policies.csv` — schema: see any existing city
3. Add one entry to `data/cities.json`

The app picks it up automatically. No changes to any Python file.

---

## Pages

| Page | What it shows |
|------|--------------|
| **Landing** | National alert banner, Kenya coverage map, enforcement gap by city |
| **Incident Map** | Folium dark map — city selector, severity markers, risk heatmap, national view |
| **Impact Analysis** | National comparison + single-city deep dive — timeline, zones, enforcement gap |
| **Policy Tracker** | National + per-city: budget utilisation, blocker taxonomy, lives at risk |
| **City Benchmarks** | Radar + scatter: Nairobi vs Medellin, Rotterdam, Jakarta, Dhaka, Singapore |
| **Risk Calculator** | Site-level composite risk score — Kenya-wide city presets included |
| **Community Report** | Citizen incident submission — all 25 cities, SMS gateway in roadmap |

---

## Risk calculator weights

| Component | Weight | Notes |
|-----------|--------|-------|
| Population density | 25% | Per hectare, 0–500 normalised |
| Drainage gap | 20% | (100 - coverage%) |
| River proximity | 25% | 0–500m band |
| Riparian violation | 15% | Full weight if non-compliant |
| Flat terrain | 10% | Slope < 10% |
| Soil impermeability | 5% | Clay=1.0, sandy=0.0 |

Calibration partners needed: JKUAT, UoN Civil Engineering, WRMA, county engineering departments.

---

## Extension roadmap

- **Real-time rainfall**: KMD API (`api.meteo.go.ke`) or OpenWeatherMap — replace hardcoded alert banner
- **WRMA gauge data**: River levels for Tana, Nzoia, Nyando, Ewaso Ng'iro, Athi, Mathare
- **SMS community reports**: Africa's Talking via [kenya-sms](https://github.com/gabrielmahia/kenya-sms) — removes web access barrier for Mathare, Kibera, Garissa, Budalangi, Mandera
- **Ward-level granularity**: 85 Nairobi wards × sitting MCAs = political accountability at individual level
- **Supabase migration**: When community reports exceed ~500 rows or concurrent writes needed
- **Cross-border coordination tracker**: Daua (Mandera/Ethiopia/Somalia), Nzoia (Kenya/Uganda), Migori (Kenya/Tanzania)

---

## Real data sources

| Source | Data | Access |
|--------|------|--------|
| Kenya Meteorological Department | Rainfall, forecasts | api.meteo.go.ke |
| Water Resources Authority | River gauges, basin data | wrma.go.ke |
| NDMA | Drought/flood contingency data | ndma.go.ke |
| Nairobi City County | Incident reports, drainage maps | FOIA / open data |
| NDOC | Disaster declarations | Public reports |
| Kenya Open Data Portal | Ward boundaries, census | opendata.go.ke |
| Humanitarian Data Exchange (HDX) | Settlement boundaries | data.humdata.org |
| LVBC | Lake Victoria basin data | lvbcom.org |
| Kenya Red Cross | Situation reports | redcross.or.ke |

---

## Database migration

Current: flat CSV per city (works to ~500 community reports per city).
Migration path: **Supabase** (PostgreSQL, free tier, row-level security).

```python
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)
incidents = client.table("incidents").select("*").eq("city_id","nairobi").execute().data
```

Store in `.streamlit/secrets.toml`.

---

## IP & Collaboration

**Owner:** Gabriel Mahia — `contact@aikungfu.dev`
**License:** CC BY-NC-ND 4.0 — attribution required, no commercial use, no derivatives without permission.
Data contributions (new cities, corrections with source citations) welcome via Issues.

---

*Part of the [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack) East Africa engineering ecosystem.*
*Inspired by OpenResilience Kenya, Rotterdam Delta Programme, 100 Resilient Cities.*
---

## Portfolio

Part of a suite of civic and community tools built by [Gabriel Mahia](https://github.com/gabrielmahia):

| App | What it does |
|-----|-------------|
| [🌊 Mafuriko](https://floodwatch-kenya.streamlit.app) | Flood risk & policy enforcement tracker — Kenya |
| [💧 WapiMaji](https://wapimaji.streamlit.app) | Water stress & drought intelligence — 47 counties |
| [🏛️ Macho ya Wananchi](https://civic-decoder.streamlit.app) | MP voting records, CDF spending, bill tracker |
| [🌾 JuaMazao](https://mazao-intel.streamlit.app) | Live food price intelligence for smallholders |
| [🏦 ChaguaSacco](https://sacco-scout.streamlit.app) | Compare Kenya SACCOs on dividends & loan rates |
| [🛡️ Hesabu](https://budget-sentinel.streamlit.app) | County budget absorption tracker |
| [🗺️ Hifadhi](https://hifadhi.streamlit.app) | Riparian encroachment & Water Act compliance map |
| [💰 Hela](https://hela.streamlit.app) | Chama management for the 21st century |
| [💸 Peleka](https://remit-lens.streamlit.app) | True cost remittance comparison — diaspora to Kenya |
| [📊 Msimamo](https://quantum-maestro.streamlit.app) | Macro risk & trade intelligence terminal |
| [🦁 Dagoretti](https://dagoretti-community-hub.streamlit.app) | Alumni atlas & community hub for Dagoretti High |
| [⛪ Jumuia](https://catholicparishsteward.streamlit.app) | Catholic parish tools — church finder, pastoral care |

