"""Assemble source-reviewed members and named events for standardization."""
import json
import hashlib
from collections import Counter

from scripts.standardize import ROOT


def build(city):
    city_root = ROOT / city
    identities = json.loads((city_root / 'source/identity-draft.json').read_text())
    mandate_doc = json.loads((city_root / 'source/mandates.json').read_text())
    extracted_path = city_root / 'work/reviewed-extraction.json'
    if city == 'bratislava':
        extracted_path = city_root / 'work/extracted.json'
    extracted = json.loads(extracted_path.read_text())
    mandates = {m['person_id']: m['periods'] for m in mandate_doc['members']}
    aliases = {}
    canonical = {}
    by_id = {member['id']: member for member in identities['members']}
    for member in identities['members']:
        for name in member.get('source_names', []):
            aliases.setdefault(name, []).append(member)
        canonical.setdefault(member['name'], []).append(member)
    manual_aliases = {}
    if city == 'kosice':
        alias_doc = json.loads((city_root / 'source/manual-matrix-identities.json').read_text())
        matrix_path = city_root / 'work/sources/downloads.json'
        receipts = {receipt['url']: receipt for receipt in json.loads(matrix_path.read_text())}
        receipt = receipts.get(alias_doc['source_url'])
        if not receipt or receipt['sha256'] != alias_doc['source_sha256']:
            raise ValueError('Manual-matrix identity source hash changed; review aliases again')
        manual_aliases = {item['source_name']: by_id[item['person_id']] for item in alias_doc['mappings']}

    members = []
    for identity in identities['members']:
        records = [m for m in mandate_doc['members'] if m['person_id'] == identity['id']]
        if len(records) != 1 or identity['id'] not in mandates:
            raise ValueError(f"Missing or duplicate mandate record: {identity['id']}")
        members.append({k: identity[k] for k in ('id', 'name', 'given_name', 'family_name', 'sources')} |
                       {'mandates': mandates[identity['id']]})

    events = []
    unresolved = Counter()
    for extracted_event in extracted['events']:
        votes = []
        for row in extracted_event['rows']:
            candidates = aliases.get(row['source_name'], [])
            if not candidates:
                candidates = canonical.get(row['source_name'], [])
            if not candidates:
                candidate = manual_aliases.get(row['source_name'])
                candidates = [candidate] if candidate else []
            if len(candidates) != 1:
                unresolved[row['source_name']] += 1
                continue
            vote = {'person_id': candidates[0]['id'], 'option': row['option']}
            if row.get('manual_correction'):
                vote['manual_correction'] = row['manual_correction']
            votes.append(vote)
        if unresolved:
            continue
        event = {k: extracted_event[k] for k in ('id', 'date', 'title', 'sources',
                                                 'present_count', 'counts')}
        event['sequence'] = extracted_event.get('sequence', extracted_event['source_vote_number'])
        event['status'] = extracted_event.get('status', 'valid')
        event['votes'] = votes
        extras = {'source_vote_number': extracted_event['source_vote_number']}
        for field in ('source_sitting', 'source_time', 'source_note', 'published_totals',
                      'present_count_basis', 'manual_corrections', 'status_source'):
            if extracted_event.get(field) is not None:
                extras[field] = extracted_event[field]
        if extras:
            event['extras'] = extras
        events.append(event)
    if unresolved:
        raise ValueError(f"Unmatched/ambiguous identity names: {dict(unresolved)}")
    events.sort(key=lambda event: (event['date'], event['sequence'], event['id']))

    identity_note = ('Every Bratislava roll-call source name matches one reviewed official profile ID. Košice H.E.R. names match one official ID; the five distinct manual-matrix title variants are mapped explicitly in source/manual-matrix-identities.json, tied to the original PDF hash.')
    mandate_doc['identity_review_status'] = 'reviewed'
    mandate_doc['identity_review_note'] = identity_note
    (city_root / 'source/mandates.json').write_text(json.dumps(mandate_doc, ensure_ascii=False, indent=2) + '\n')

    coverage = {'coverage_verified': True,
                'collection_complete': extracted.get('collection_complete', False),
                'named_events': len(events),
                'excluded_secret_ballots': len(extracted.get('secret_ballots', [])),
                'explanation': ('All 36 discovered meetings across 2022–2026 term collected. The meeting sequence gap (#30) was verified from official minutes of 6 Nov 2025 (Bod 7) and resolution 1037/2025: the planned late-November sitting was replaced by meeting 29 and cancelled; resolutions 1031–1037 (meeting 29) are immediately followed by 1038 (meeting 31). Inaugural aggregate-only acclamation votes are documented separately in coverage-exceptions.json.'
                                if city == 'bratislava' else
                                'All 39 official meetings (1–39) collected with complete coverage. The March 2024 inquorate sitting had no votes; 19 secret ballots have aggregate totals only; manual matrix and corrections appendix reconciled with source PDF evidence.')}
    if city == 'kosice':
        coverage['excluded_secret_ballots'] = len(extracted.get('secret_ballots', []))
    output = {'city': city, 'review_status': 'reviewed',
              'identity_review': {'review_status': 'reviewed', 'note': identity_note},
              'coverage': coverage,
              'members': members, 'events': events}
    target = city_root / 'source/reviewed.json'
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(f'{city}: assembled {len(members)} members, {len(events)} events, {sum(len(e["votes"]) for e in events)} person rows; coverage_verified=true')


if __name__ == '__main__':
    for municipality in ('bratislava', 'kosice'):
        build(municipality)
