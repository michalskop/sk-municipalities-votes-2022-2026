# Reviewed input contract

Create `<city>/source/reviewed.json` after extracting and checking official roll
calls. This is an interchange format for reviewed extraction, not an official API.
No example below is real municipal data.

```json
{
  "city": "kosice",
  "review_status": "reviewed",
  "members": [{
    "id": "kosice:person:source-id-123",
    "name": "Example Person",
    "given_name": "Example",
    "family_name": "Person",
    "sources": [{"url": "https://example.org/roster"}],
    "mandates": [{
      "since": "2022-11-11",
      "until": null,
      "sources": [{"url": "https://example.org/mandate"}]
    }]
  }],
  "events": [{
    "id": "2025-12-12-001",
    "date": "2025-12-12",
    "title": "Example motion",
    "status": "valid",
    "sources": [{"url": "https://example.org/roll-call.pdf", "note": "Page 1"}],
    "present_count": 1,
    "counts": {"yes": 1, "no": 0, "abstain": 0, "not_voting": 0, "absent": 0},
    "votes": [{"person_id": "kosice:person:source-id-123", "option": "yes"}]
  }]
}
```

Use stable, city-scoped person IDs backed by source identifiers or a reviewed
identity mapping. Never merge people solely by normalized names. Each event ID
must distinguish the sitting/continuation and vote number. Document source page
numbers, raw option labels, and any count derivations in source notes.

Mandate `since` and optional `until` are inclusive ISO dates. End a predecessor's
mandate and start the replacement's using official evidence; overlapping mandates
for one person fail validation. Same-day oaths/replacements can use `since_event`
or `until_event`, referencing an included event on the boundary date. All events
on that date must then have distinct positive `sequence` integers reflecting
reviewed official order. Boundaries are inclusive. Store their evidence in the
mandate sources; no timestamp is invented. Missing/unreviewed event order fails.
The shared attendance engine counts only supplied eligible person votes, so a
new member's denominator excludes earlier events on the same date.

Each event must explicitly list every active member once. Missing rows fail;
they are not converted into absences. `not_voting` preserves the explicit source
nonvoting label; it does not prove physical presence. `absent` preserves recorded
absence. Preserve this distinction even
where a dashboard chart groups neutral options. Unknown source options fail.

All five counts and the present total must be reconciled with the source. If a
count is derived from the roster rather than directly published, record that
method in the source note. Event status is explicitly `valid`, `invalid`, `test`,
or `other`; the shared attendance engine excludes `invalid` and `test`.

The converter validates **every** record against local upstream JSON schemas,
including the assembled `all-members` analysis input, before writing the six
standard tables. Date-only sources remain date-only; no time of day is invented.

`present_count` is the **source's** aggregate, not a universal attendance formula.
Košice's H.E.R. reports count only `yes`, `no`, and `abstain` in their present
total; the missing total includes both `absent` and `not_voting`. Bratislava's
source presence includes nonvoting. Each city's `source_present_options` controls
reconciliation, with `source_present_options_by_date` documenting the June 2023
Košice exception, including its after-midnight continuation. The analysis uses `attendance_present_options` and
`attendance_absent_options`: both cities follow NR SR by excluding nonvoting from
voting participation. A physically present person can therefore score zero for
participation in that vote.

Extracted drafts retain original names, card/row numbers, club labels, and source
times. These are observations, not stable IDs or mandate boundaries. Supply an
explicit reviewed identity mapping before assembling this input. In particular,
source name spelling can change, cards can be zero, and card numbers are not person IDs.
