# Vote dashboard CPU incident, 13 October 2026

Vercel disabled `mesta.datatimes.sk` after its Hobby team exceeded Active CPU
usage. The website's individual vote loader rebuilt a whole city's voting history
from a 5–6 MB CSV on every request, processing 75,000–85,000 votes to display one
event. Server-side layout query handling forced dynamic rendering. Production
build logs showed that the intended fetch cache rejected the large CSV and event
JSON: their serialized cache entries exceeded Next.js's 2 MB limit.

The costly request path is confirmed; the traffic source behind the spike is
unconfirmed because the historical runtime logs expired. Upgrading hosting
capacity does not remove the implementation defect.

Standardization now generates bounded files under `CITY/data/dashboard`: summary
shards for the index and one JSON file per vote. All have an enforced 1 MB UTF-8
budget. Detail files preserve the reviewed ballots, historical club assignments,
source URLs and extraction metadata. The dashboard reads one detail file, uses
ISR, switches visual layouts in the browser and disables bulk detail prefetching.
Default-language votes have an explicit route because local Next.js 15.5.12 tests
found that middleware-rewritten on-demand paths bypassed the page cache.

The shared dashboard repository contains the full explanation, audit of the other
apps, and release checklist:
[Vote dashboard performance](https://github.com/michalskop/legislature-dashboard/blob/main/docs/vote-dashboard-performance.md).
Read it before copying a dashboard or enabling a new parliament's votes.

Regression tests verify every published ballot and summary against the standard
tables, source metadata preservation, club date boundaries, withdrawn events,
neutral vote counts, safe event filenames and artifact-size limits. Frontend tests
verify single-event fetches and reject invalid/cross-city IDs before fetching.
Release checks must also prove real cache hits for both default and prefixed
language routes and zero page/RSC/data requests during layout switching.
Run the shared `scripts/check-vote-cache.cjs` and optional Python Playwright
`scripts/check-vote-browser.py` from the dashboard app against a clean build and
the live site. Do not use `force-static` to mask presentation query handling:
server/browser search parameters can then disagree and break deep-link hydration.

## Verified rollout

Dashboard commit `b588e14` deployed the CPU remediation on 14 October 2026 to
Vercel project `legislature-dashboard-sk-cities`, aliased to `mesta.datatimes.sk`.
Commit `4d8c1af` preserves Suspense hydration for layout deep links and adds a
reusable browser regression for deep links and Back/Forward.
Production build logs have no oversized-cache warnings. HTTP smoke checks
returned `x-vercel-cache: HIT` for representative Slovak and English vote paths,
both with and without layout query parameters. All 39 data tests and six
frontend request tests passed, along with type checking, lint and the build.
