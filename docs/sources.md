# Official source research

Checked on **2026-10-11** through browsing and direct collection using the
environment's approved command paths. Original PDFs/HTML are preserved with
hashes and timestamps. Original-source regression fixtures now complement the
earlier browsing extracts. A rendered encoded-font page was visually checked.
Full-term source coverage and reviewed identities remain separate requirements.

## Bratislava

- [Official meeting archive](https://zastupitelstvo.bratislava.sk/).
- [18 June 2026 meeting](https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-18062026/)
  exposes Program, Hlasovania, Účasť, Záznam, and Uznesenia tabs and links minutes.
- The Hlasovania link contains a meeting-specific `rokovanie_tab_<id>=2`
  parameter. Original collection confirms the cookie-dependent tab transport
  and named voting panels. The linked minutes are also preserved as originals;
  use them to review procedural context and oath order.
- Older 2022 URLs lack the `2022-2026` slug. Use the council's actual inauguration
  and mandate dates to exclude votes of its predecessor. The term's inauguration
  was 15 November 2022, supported by [resolution 1/2022](https://zastupitelstvo.bratislava.sk/297353-sk/uznesenia/uznesenie/).
  Delayed oaths and subsequent replacements are documented in [mandate evidence](mandates.md).
- The inaugural minutes record three aggregate acclamation votes, each with 43
  yes and no individual choices. The reviewed coverage exception preserves the
  minutes and page references; the aggregate votes are excluded from named rows.
- Verify archive pagination and term selectors. The first page is not full coverage.
- The apparent sequence gap between meeting 29 (6 November 2025) and meeting 31
  (11 December 2025), with number 30 omitted from the archive listing, is fully
  resolved. The minutes of meeting 29 (Bod 7, page 100) and resolution 1037/2025
  confirm that the late-November sitting originally scheduled as number 30 was
  replaced by the 6 November sitting, and no further November sitting took place.
  Council resolutions are strictly continuous across this boundary: meeting 28
  ended at resolution 1030/2025, meeting 29 adopted resolutions 1031/2025 through
  1037/2025, and meeting 31 started at resolution 1038/2025 (through 1096/2025).
  Full term coverage for all 36 held meetings is verified.
- [14 December 2023, agenda item 20](https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-14122023/bod-20/)
  publishes named lists for vote 32: 29 yes, zero no/abstain, three nonvoting,
  and 13 absent, accounting for all 45 members. This indexed HTML content is saved
  in `bratislava/source/extracts/` and covered by the adapter's regression tests.
  HTML named lists avoid the garbled font encodings in some PDF annexes.
- Original agenda pages require their observed `bod-typ-<id>=hlasovania` link.
  The tab sets session state and redirects; collection must preserve cookies.
  `.panel.hlasovania` contains named lists with official person-profile links.
  The original HTML reproduces vote 32 and its 45 distinct person identifiers.
- The full meeting voting tab also contains procedural votes without agenda
  items and paginates its named panels. Bootstrap the voting-tab cookie before
  following bare `?page=` links. Combining tab selection and pagination resets
  the page during redirection. Receipts record `view_context`, so identical URLs
  can have separate program and voting originals.
- The [29 May 2025 minutes and annex](https://zastupitelstvo.bratislava.sk/data/att/308/98041.eeb71d.pdf)
  contain member/group rows, but text extraction corrupts parts of the names and
  headings. Do not repair identities automatically by guessing shifted characters.

## Košice

All 39 archive entries and their 101 voting PDFs have been collected. The H.E.R.
adapter reconciles 2,075 named draft events, including six votes transcribed from
the 28 October 2024 manual matrix. Its first column is an attendance check
(37 present, no choices cast); columns 2–6 are unanimous yes votes. Twenty-six
correction pages yield 42 named overrides and two invalid-event markings in
`kosice/source/corrections.json`, with original hashes, pages, and text retained.
Nineteen secret ballots remain aggregate-only. These records still need final
mandate, event, and coverage review before standardization.

- [Official 2022–2026 archive](https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026)
  includes ordinary, extraordinary, and continued sittings.
- [Opening sitting, 11 November 2022](https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/zasadnutie/1)
  links voting PDFs for votes 1–20 and 21–29, plus aggregate results and attendance.
  Preserve both files; one sitting can have multiple vote documents.
- [12 December 2025 sitting](https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/zasadnutie/34)
  links votes 1–13. Browsing the voting PDF failed with a cache miss; inspect the
  actual document before implementing its parser.
- [5 October 2026 sitting](https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/zasadnutie/39)
  links votes 1–9. Do not stop collection at the most recent ordinary sitting.
- The [opening-session report, votes 21–29](https://static.kosice.sk/meeting/vote/o7KRUTVCfzGUFDOZp/CLIo1zL8GhC59Ofne2w/FtsurQh83ccJW4/hlasovanie_111122_21_29.pdf)
  is readable through browsing. Its nine events reconcile all 41 named rows with
  the published counts. Nonvoting is included in the source's missing total,
  even when a nonzero card is shown. Vote 21 has 39 participating and two
  nonvoting members; there are zero explicit absent rows.
- [27 February 2025, vote 49, PDF page 9](https://static.kosice.sk/meeting/vote/18neCDSndmaEenNu/1BP5a2ASpWP4OFybSWL/P3FmDRddG2eKrOu8v/hlasovanie270225_41_60.pdf)
  has 31 yes, four nonvoting and six absent rows. It also supplies dated labels:
  Košický klub, Spolupráca pre Košice, Starostovia a nezávislí kandidáti, and
  Nezaradení. These are point-in-time observations; no continuous membership
  periods or governing coalition have yet been inferred from them.
- Some June 2023 PDFs lack Unicode maps for embedded Arial fonts. Recover maps
  from embedded TrueType cmap tables in a temporary PDF, preserving originals.
  Do not repair names by arbitrary character shifts. Blank card fields occur
  on explicitly absent rows; group labels sometimes wrap across two lines.
- The 13 June 2023 sitting, continuing after midnight on 14 June, counts
  nonvoting in aggregate presence. Date-specific config records the original
  evidence; participation analysis still excludes nonvoting.
- The 22 March 2024 minutes confirm no quorum (18 members) and termination
  without votes. Its separate 27 March continuation has 16 named votes.

## Decisions still requiring evidence

Extend original-source fixtures to manual voting, corrections, and newly encountered
layouts. Verify dated mandates and replacements before deriving
absence. Research dated council clubs separately from 2022 electoral affiliation;
do not import national parliamentary groups. Document coalitions and changes
before enabling political metrics. Reuse rights/licensing have not been confirmed.
