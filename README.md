# Slovak municipal votes, 2022–2026

Preparing named votes of the **city assemblies of Bratislava and Košice** for
**mesta.datatimes.sk**, following the sibling
[`cz-municipalities-votes-2022-2026`](../cz-municipalities-votes-2022-2026).
This covers council decisions, not election results or city-district assemblies.

**Status:** originals have been collected for **36 Bratislava and 39 Košice archive
entries**. The adapters extract **3,746 named draft events (160,282 individual
votes)**. A Košice manual matrix remains unresolved, 19 secret ballots lack
individual options, and 26 correction appendices require review. Original
PDF/HTML regression fixtures and reviewed
source facts about replacements are included. Full-term
coverage and identity/mandate review are still incomplete. No production
dataset has been published. The Slovak
dashboard starts with preparation cards and official-source links. Club,
coalition, and WPCA metrics are disabled.

## Structure

```text
bratislava/, kosice/
  config/sources.json       official sources and research status
  source/reviewed.json      reviewed input; added after extraction
  work/                    downloaded originals and intermediate files; ignored
  data/                    validated standard CSV/JSON; generated after review
  analyses/attendance/     shared-engine definition and output; generated
scripts/                   collection, standardization, analysis, dashboard staging
tests/                     quality-gate tests and original-source regression fixtures
dashboard/overrides/       Slovak configuration/content over the Czech dashboard
docs/                      source research, input contract, and implementation plan
```

## Local commands

Python 3.10+; install dependencies in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m scripts.collect_sources kosice --limit 1
.venv/bin/python -m scripts.collect_sources bratislava
```

Collection needs network access. Downloads retain URLs, retrieval timestamps,
and SHA-256 hashes. Review discovery completeness before claiming term coverage.
Interrupted collection reuses hash-verified files downloaded that day; use
`--refresh` to fetch them again. Later runs re-fetch previous-day sources.
The collector inventories and downloads source files. Separate adapters extract
person-level votes into drafts, with source-count reconciliation:

```bash
python3 -m scripts.extract_kosice kosice/source/extracts/2022-11-11-votes-21-29.json --out kosice/work/opening.json
python3 -m scripts.extract_kosice kosice/source/extracts/2025-02-27-vote-49.json --out kosice/work/later.json
python3 -m scripts.extract_bratislava bratislava/source/extracts/2023-12-14-vote-32.json --out bratislava/work/sample.json
```

For downloaded Košice PDFs, the adapter uses system `pdftotext -layout`; pass
`--source-url`. Bratislava HTML mode takes `--source-url` and `--date`.
Original voting panels and embedded-font PDFs are now covered by regression
fixtures. Košice font recovery uses the embedded font's Unicode cmap; it does
not guess or replace names. Secret ballots and correction appendices are retained
separately. Unknown layouts fail extraction.
Draft extraction never marks identities, mandates, or event status as reviewed.
`python3 -m scripts.audit_samples` regenerates the committed
[sample reconciliation report](docs/source-sample-audit.json), including input
hashes, per-event counts, and source references.
See [source research](docs/sources.md) and [remaining work](docs/implementation-plan.md).

Extract an entire completed or interrupted collection into a draft and coverage
report, keeping source failures visible:

```bash
python3 -m scripts.extract_inventory kosice
python3 -m scripts.extract_inventory bratislava
```

Results are in `<city>/work/extracted.json` and `extraction-report.json`.
These reports do not approve publication. See [mandate evidence](docs/mandates.md)
for delayed oaths, replacements, club changes, and the archive numbering gap.
`python3 -m scripts.audit_collection` checks original hashes and report freshness,
then updates [the collection audit](docs/source-collection-audit.json).

After preparing a real `source/reviewed.json` using the
[input contract](docs/input-format.md):

```bash
.venv/bin/python -m scripts.standardize kosice
.venv/bin/python -m scripts.run_attendance kosice
```

Both commands validate against locally built **Legislature Data Standard** schemas.
The attendance runner invokes the existing, unmodified shared analysis engine.
Defaults use `/home/michal/project/legislature-data/`; override with `--schemas`
and `--shared` on another machine. The upstream engine itself also needs its
sibling `legislature-data-standard/dist` directory.

Attendance follows the shared Slovak parliament convention: `yes`, `no`, and
`abstain` count as participation; `not_voting` and `absent` do not. Raw options stay
distinct. Source aggregate presence is city-specific: Košice excludes nonvoting,
while Bratislava includes it. See [source research](docs/sources.md).

## Dashboard preparation

```bash
python3 -m scripts.prepare_dashboard --out /tmp/sk-cities-dashboard
cd /tmp/sk-cities-dashboard
pnpm install
pnpm --filter @legislature/sk-cities dev
```

Node.js 20+ and pnpm 10.33.2. The script composes `apps/sk-cities` from
`/home/michal/project/legislature-dashboard/apps/cz-cities`, applies Slovak
overrides, and copies shared packages into an isolated preview. It never changes
the existing project checkout. Use `--reuse-dependencies` for local checks with
its installed dependencies; those symlinks are for local QA only.

See [dashboard integration](dashboard/README.md) for build and deployment settings.
`AGENTS.md` is preserved as requested; this README describes the actual new tooling.
