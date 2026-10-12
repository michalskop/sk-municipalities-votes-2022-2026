# Identity and mandate evidence

Checked on 11 October 2026 against official sources. The structured roster
observations retain source identifiers and original-byte hashes. They are drafts,
not a reviewed mandate registry. Original roster HTML is in each city's
`work/rosters/`. Do not use voter cards as identifiers.

Reviewed mandate periods for all 47 Bratislava identities and 41 Košice members
are recorded in each city's `source/mandates.json`. The reviewed inputs use those
periods only after every named row maps to one official profile ID and the full
event roster passes standardization. The source identity drafts remain unchanged.

## Bratislava

[Resolution 1/2022](https://zastupitelstvo.bratislava.sk/297353-sk/uznesenia/uznesenie/)
lists 45 elected councillors. Jozef Krúpa and Michal Vlček did not take their
oaths at the inaugural sitting. [29 November 2022 minutes, printed pages 25–26](https://zastupitelstvo.bratislava.sk/data/att/65270.pdf)
confirm their oaths and resolution 2/2022. Record their start separately from
15 November. Original named lists omit both in votes 1–6 (43 members) and
include them from vote 7, the vote on resolution 2/2022 (45 members).
Their identity drafts record `since_event: 2022-11-29-007`; a reviewed input
must also assign the official sequence numbers on that date.

The [official council roster](https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026/)
also retains former members and the mayor. Exclude the mayor from councillor
roll calls. It records:

- Michal Sabo's resignation on 15 December 2023; Pavol Škápik's arrival on
  29 February 2024. [Resolution 427/2024](https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-29022024/bod-1/)
  corroborates the replacement and oath.
- Jakub Kuruc's resignation on 15 April 2024; Elena Pätoprstá Smatana's arrival
  on 25 April 2024. The minutes place Elena's oath before the roll calls; her
  boundary is vote 1 (`2024-04-25-001`), where the source records her absent.
  Škápik's 29 February 2024 minutes likewise place his oath before vote 1
  (`2024-02-29-001`). Both are active at the first event even when a vote row
  records an absence.

Voting panels link directly to official profiles. Most profiles carry numeric
IDs; Elena's uses a slug. Preserve the complete URL in either case.

The 29 November 2022 minutes place Jozef Krúpa and Michal Vlček's oaths before
vote 7 (`2022-11-29-007`); the first six events have 43 members and later events
have 45. Sabo and Kuruc's replacements are dated to the day before their
official resignation dates under the inclusive mandate-period convention.

## Košice

The [official roster](https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/poslanci)
provides 41 source profile IDs. Compare these with every historical roster;
academic titles and spellings differ, including Karafa/Karaffa, Petrovčík/Petrovčik,
and the opening report's Erok/Erik Weiss. The five distinct title variants in
the October 2024 manual matrix are mapped to official IDs in
`source/manual-matrix-identities.json`, with the original PDF hash.

The [official changes log](https://www.kosice.sk/obcan/zmeny-v-poslaneckom-zbore-mz-v-priebehu-volebneho-obdobia-r-2022-2026)
records club changes: eight members joined Spolupráca pre Košice on 11 May 2023;
Bačinský and Vrchota joined Košický klub on 13 June 2023; Lasky joined
Spolupráca on 12 March 2024; Karabin became unaffiliated on 25 June 2024,
Bačinský on 1 December 2025, and Vrchota on 16 September 2026. These are club
changes, not council mandate changes or coalition evidence.

## Publication checks

The official Bratislava archive lists 36 meetings with numbers 1–37,
omitting number 30. This gap has been investigated and resolved: meeting 30
was an originally scheduled late-November 2025 sitting that was replaced by
the 6 November 2025 sitting (meeting 29, Bod 7, resolution 1037/2025) and
subsequently cancelled. Resolution numbering is unbroken across the boundary:
meeting 28 ended at resolution 1030/2025, meeting 29 covered 1031–1037/2025,
and meeting 31 resumed at 1038/2025. The 15 November 2022 inaugural minutes
were reviewed: they record three aggregate acclamation votes (43 yes each)
without individual options. Both facts are preserved in
`bratislava/source/coverage-exceptions.json`; aggregate votes are not invented
as named events.
Košice's 22 March 2024 minutes confirm an inquorate sitting with 18 members;
no voting PDF is expected. Treat the 27 March continuation separately.
All 39 official Košice meetings (1–39) are collected and verified.
