# Contributing

## Data contributions
- All changes to `incidents.csv` and `policies.csv` must include a source citation in the PR description.
- The `resilience_score` in `city_benchmarks.json` is manually curated — changes require a documented rationale.
- New benchmark cities must include `transferable` lessons specific to Nairobi's context.
- The `blocking_factor` field in policies is intentionally qualitative. Do not normalise to an enum without discussion.

## Community report data
`data/community_reports.csv` is excluded from git via `.gitignore` — it contains potentially sensitive location data.

## Code contributions
Open an Issue before large PRs. Discuss architecture changes before implementing.
