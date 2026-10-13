# Slovak city dashboard overlay

The user-requested integration target is the existing Next.js
`/home/michal/project/legislature-dashboard` monorepo. This repository stores only
the Slovak changes; `scripts.prepare_dashboard` composes them over `apps/cz-cities`
in an isolated output directory. It records the template Git revision in
`TEMPLATE.json` and fails when required transformation markers have changed.

## Cached vote pages

Standardization now writes `CITY/data/dashboard/index.json`, small summary
shards, and `vote-events/IDENTIFIER.json` detail files. These contain reviewed
ballots, names and historical club affiliations; detail files retain source
URLs and extraction metadata. Every artifact has a 1 MB size limit, below
Next.js's 2 MB cache-entry limit after serialization.

To regenerate these files from already standardized tables:

```bash
python3 -m scripts.dashboard_votes bratislava
python3 -m scripts.dashboard_votes kosice
```

The web app fetches one detail file per vote and generates that page on its
first visit, caching it with hourly revalidation. Layout selection uses browser
history and does not request another server render. The vote index reads only
summary shards and disables automatic detail-page prefetching. Publish data
artifacts before deploying the frontend that consumes them.

Frontend request regressions: `node scripts/test-vote-fetch.cjs` from the app
directory. `SK_DATA_BASE` and `SK_PUBLISHED_CITIES` must be included in the
dashboard's Turbo build environment so build cache keys reflect their values.

The generated `apps/sk-cities` uses shared UI, charts, utilities, and parliament
types. Default URLs are `/`, `/bratislava`, `/kosice`; English uses `/en/...`.
Pending cities appear on the landing page but have no active dataset routes.
Only attendance is enabled initially, and disabled analyses are never fetched.
No Czech fixtures, memberships, party brands, Matomo ID, or analysis results are copied.
The preview uses the existing serif fallback rather than downloading Google fonts.

## Verification

```bash
python3 -m scripts.prepare_dashboard --out /tmp/sk-cities-dashboard --reuse-dependencies
cd /tmp/sk-cities-dashboard/apps/sk-cities
node node_modules/typescript/bin/tsc --noEmit
node node_modules/next/dist/bin/next build --no-lint
```

Use a fresh output path each time. Without `--reuse-dependencies`, run `pnpm install`
at the generated monorepo root before checking/building. Dependency symlinks in the
QA variant must not be copied into the actual monorepo or deployment bundle.
The verified local build uses `--no-lint`: reused dependencies lack the inherited
ESLint react-hooks plugin. Type checking and production compilation still run.
After a fresh `pnpm install`, run the normal build and lint separately.

## Integration and hosting

Copy the generated app's source/config into `legislature-dashboard/apps/sk-cities`
once that checkout is writable, excluding `node_modules/`, `.next/`, and
`*.tsbuildinfo`. Shared packages already exist there. Run `pnpm install` to update
the original workspace lockfile and commit the app and lockfile together.

| Setting | Value |
| --- | --- |
| Root directory | `apps/sk-cities` |
| Install command | `pnpm install` |
| Build command | `cd ../.. && pnpm build --filter=@legislature/sk-cities` |
| Output directory | `.next` |
| Domain | `mesta.datatimes.sk` |
| Default language | `sk` |
| Additional language | `en` |

`SK_DATA_BASE` overrides the data repository root; its default is the intended
raw GitHub path, not a verified published repository. `SK_PUBLISHED_CITIES` is empty
by default; set `bratislava`, `kosice`, or `bratislava,kosice` only after validating
and publishing the actual city tables and attendance output. Rebuild after changes.
Use `REVALIDATE_SECRET` for the inherited revalidation endpoint; keep it outside Git.

The domain has not been deployed or configured. Club and coalition metrics,
automated refresh, and real source coverage remain work listed in
[`docs/implementation-plan.md`](../docs/implementation-plan.md).
