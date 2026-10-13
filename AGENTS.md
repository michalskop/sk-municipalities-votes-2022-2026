# Repository Guidelines: Slovak Municipal Votes (2022–2026)

## Project Purpose & Scope
This repository processes named roll-call votes and assembly data for **Bratislava** and **Košice** (2022–2026 election term) to power the Slovak municipal voting dashboard at [mesta.datatimes.sk](https://mesta.datatimes.sk).

## Workspace Structure
- `bratislava/`, `kosice/`:
  - `config/sources.json`: Official source registry and configuration.
  - `source/clubs.json`: Sourced political party clubs and historical member affiliations across 2022–2026.
  - `source/reviewed.json`: Extracted and verified vote data from council meetings.
  - `data/`: Standard Popolo tabular datasets (`organizations.csv`, `memberships.csv`, `persons.csv`, `vote_events.csv`, `votes.csv`).
  - `analyses/`: Generated analysis outputs validated against shared JSON schemas (`attendance`, `rebelity`, `govity`, `wpca`, `_run_status.json`).
- `scripts/`:
  - `scripts/standardize.py`: Normalizes reviewed data into standard Popolo files and prepares analysis inputs.
  - `scripts/run_analyses.py`: Orchestrates shared analysis engines (`legislature-data-analyses`), runs government axis detection, writes `_run_status.json`, and validates against schemas.
- `tests/`: Automated unit tests and source regression tests.

## Development & Pipeline Commands
Runtime: Python 3.10+
Shared analysis engines: `/home/michal/project/legislature-data/legislature-data-analyses`
Shared schemas: `/home/michal/project/legislature-data/legislature-data-standard/dist`

```bash
# Run standardization and all analyses for a city:
python3 -m scripts.run_analyses bratislava
python3 -m scripts.run_analyses kosice

# Run unit tests:
python3 -m unittest discover -s tests -v
```

## Dashboard & Domain Integration
- Frontend dashboard: `apps/sk-cities` in `/home/michal/project/legislature-dashboard`.
- Production deployment: Vercel project `legislature-dashboard-sk-cities` (formerly `legislature-dashboard`) aliased to `mesta.datatimes.sk`.
- Cloudflare DNS requirement: `mesta.datatimes.sk` must be configured as **CNAME `cname.vercel-dns.com`** with **Proxy status: DNS only (Grey cloud ☁️ OFF)**. Enabling Cloudflare Proxy causes Error 525 (SSL handshake failed) with Vercel.

## Analysis Rules & Constraints
1. **Shared Engines**: Never fork or rewrite core analysis calculation formulas. Always invoke the shared engine scripts in `legislature-data-analyses`.
2. **Coalitions & Administration Groups**:
   - Bratislava: Coalition majority club `team-bratislava-ps-sas`.
   - Košice: Mayor & administration faction club `spolupraca-pre-kosice`.
3. **Government Axis**: Determined via point-biserial correlation with government club membership across WPCA dimensions.
4. **Data Provenance**: Always preserve source URLs, extraction hashes, and dates for all council documents.
5. **Dashboard Vote Performance**: Read `docs/dashboard-cpu-incident.md` before changing vote exports or composing another dashboard. Publish bounded per-event files and separate summary shards; never reconstruct a whole vote history inside a detail request. Preserve provenance and verify actual page-cache hits across language routes and browser-only layout switching.
