# Implementation and publication plan

## Completed preparation

- Read the Czech municipal project, dashboard, data analyses, and data standard.
- Identify official city-assembly sources and record unresolved extraction details.
- Add source inventory/download tooling with originals, URLs, timestamps, and hashes.
- Implement reviewed-input standardization, identity/mandate/tally checks, and
  validation against the existing DT schemas.
- Connect the unmodified shared attendance engine; synthetic integration verified.
- Prepare a Slovak/English `apps/sk-cities` overlay reusing the Czech dashboard.
  City dashboards are disabled by default, with preparation cards on the landing page.
- Add separate source adapters and pinned real-source extracts: nine opening
  Košice votes, one later Košice vote with club labels, and one Bratislava HTML vote.
  All 455 rows reconcile with published option counts and city-specific presence.
- Correct nonvoting participation semantics to match the shared NR SR analysis.
- Extend Bratislava collection to agenda pages, pagination, and voting-tab links;
  preserve download receipts even if subsequent requests fail.
- Collect original sources for all 36 discovered Bratislava and 39 Košice archive
  entries, preserving full meeting voting pagination and cookie/view context.
- Extract 1,677 Bratislava and 2,075 Košice named draft events (160,528 individual
  rows). Keep 19 secret ballots aggregate-only and preserve correction provenance.
- Add a source-backed adapter for the 28 October 2024 Košice six-column matrix:
  six events, 41 rows each, including the attendance check distinguished from
  five unanimous votes. Reconcile and record 42 named corrections and two
  invalid-event statuses from all 26 appendix pages.
- Review Bratislava's inaugural minutes and record three aggregate-only
  acclamation votes as a coverage exception; no individual choices are inferred.
- Recover PDF Unicode maps from embedded TrueType fonts, without guessed name
  substitutions. Add original-source regression fixtures and visually check an
  encoded-font page.
- Record official person IDs, identity drafts (47 Bratislava, 41 Košice), dated
  replacement/club evidence, and an inquorate sitting exception.
- Support sourced same-day mandate boundaries by reviewed event sequence; the
  shared attendance formula remains unchanged.
- Resolve dated mandate periods for 88 members, including same-day oath
  boundaries. Build both cities' standard tables and validate attendance outputs
  with the unchanged shared engine.
- Integrate the preparation app into the writable dashboard checkout at
  `apps/sk-cities`; routes stay disabled until reviewed data is published.
- Verification: 35 tests pass, including shared-engine integration on synthetic
  inputs; the app typecheck passes. Integrated production build, lint, and
  real-data/browser verification remain pending.

## Next: real source extraction

1. Resolved Bratislava's missing archive number 30: official minutes (meeting 29, Bod 7)
   and unbroken resolution sequence (1030 -> 1031–1037 -> 1038) confirm meeting 30 was a
   cancelled sitting replaced by meeting 29. Inaugural aggregate-only votes and sequence gap
   are documented in coverage-exceptions.json. Full-term coverage verified.
2. Verify every source exception, including June 2023 presence semantics and
   votes after midnight. Both original adapters now have regression fixtures.
3. Pin manually checked real golden samples: opening, ordinary and extraordinary
   meetings, split vote files, abstentions, nonvoting, replacements, and invalid/test votes.
4. Review source-count deltas for every manual override and publish only after the
   archive and secret-ballot coverage limits are accepted or resolved.
5. Reconcile every event's person votes with official counts; document remaining gaps.

Standardization passes for both source-reviewed inputs against the existing
schemas. Shared attendance outputs validate for 47 Bratislava and 41 Košice
members. Term coverage is verified for both cities and city routes remain disabled
in the dashboard pending publication approval.

## Next: political analyses and automation

- Establish dated club memberships and coalition composition from cited sources.
  Keep electoral affiliation distinct from council club membership.
- Add rebelity, govity, and WPCA definitions and runners that invoke the shared
  engines; never fork their analysis formulas into this repository.
- Enable each dashboard metric only once its inputs and definition are verified.
- Add nightly CI only after extraction, golden samples, schemas, and coverage checks
  pass. Refresh data on a working branch and publish all files together; failed
  downloads or validation must not overwrite the last good published dataset.
- Record successful refresh timestamps separately from newest vote dates.

## Next: dashboard QA and deployment

Install the new app's workspace dependencies and test enabled city routes against
the published datasets.
Check Slovak/English copy, member counts, denominators, vote charts, mobile layout,
and canonical URLs. Remove the preparation wording when the first city goes live.
Use the existing hosting architecture for `mesta.datatimes.sk`; configure the
custom domain and revalidation secret. No deployment or DNS change was made here.
