"""Reconcile Košice manual correction appendices against named draft rows."""
import json
import re
from collections import Counter
from pathlib import Path

from scripts.standardize import ROOT, source_present_options


LINE = re.compile(r'Hlasovanie č\.\s*(\d+)\s*-\s*(.*?)\s*"(ZA|ZDRŽAL SA)"', re.I)
INVALID = re.compile(r'Hlasovanie č\.\s*(\d+)\s*(?:bolo vyhlásené za\s+ZMÄTOČNÉ|-\s*ZMÄTOČNÉ|-\s*NEPLATNÉ)', re.I)
NAMES = re.compile(r'p\.\s*([^,]+?)(?=,\s*p\.|$)', re.I)


def review():
    city = ROOT / 'kosice'
    extracted = json.loads((city / 'work/extracted.json').read_text())
    inventory = json.loads((city / 'work/sources/inventory.json').read_text())
    meeting_by_document = {doc['url']: meeting for meeting in inventory['meetings']
                           for doc in meeting.get('documents', [])}
    events = {event['id']: event for event in extracted['events']}
    events_by_meeting_vote = {(event['meeting_url'], event['source_vote_number']): event
                              for event in extracted['events']}
    corrections, invalid, unresolved = [], [], []
    used = set()
    for annotation in extracted['annotations']:
        meeting = meeting_by_document.get(annotation['source_url'])
        if not meeting:
            unresolved.append({'page': annotation['page'], 'reason': 'annotation source is not attached to a meeting'})
            continue
        day = meeting['date']
        text = annotation['text']
        consumed = []
        for match in INVALID.finditer(text):
            number = int(match[1])
            event = events_by_meeting_vote.get((meeting['url'], number))
            if event is None:
                unresolved.append({'date': day, 'vote': number, 'page': annotation['page'], 'reason': 'invalid event not found'})
                continue
            invalid.append({'date': event['date'], 'meeting_date': day, 'event_id': event['id'],
                            'vote_number': number, 'status': 'invalid',
                            'source_url': annotation['source_url'], 'source_sha256': annotation['input_sha256'],
                            'page': annotation['page'], 'source_text': match[0]})
            consumed.append(match.span())
        for match in LINE.finditer(text):
            number = int(match[1])
            event = events_by_meeting_vote.get((meeting['url'], number))
            if not event:
                unresolved.append({'date': day, 'vote': number, 'page': annotation['page'], 'reason': 'corrected event not found'})
                continue
            names = [n.strip().strip(' .') for n in NAMES.findall(match[2])]
            if not names:
                unresolved.append({'date': event['date'], 'vote': number, 'page': annotation['page'], 'reason': 'correction has no named voter'})
                continue
            option = 'yes' if match[3].upper() == 'ZA' else 'abstain'
            for surname in names:
                candidates = [row for row in event['rows'] if surname.casefold() in row['source_name'].casefold()]
                if len(candidates) != 1:
                    unresolved.append({'date': event['date'], 'vote': number, 'surname': surname,
                                       'page': annotation['page'], 'reason': f'expected one source-name match, found {len(candidates)}'})
                    continue
                row = candidates[0]
                key = (event['id'], row['source_name'])
                if key in used:
                    unresolved.append({'date': event['date'], 'vote': number, 'surname': surname,
                                       'page': annotation['page'], 'reason': 'duplicate correction'})
                    continue
                used.add(key)
                corrections.append({'date': event['date'], 'meeting_date': day, 'event_id': event['id'], 'vote_number': number,
                                    'source_name': row['source_name'], 'source_option': row['option'],
                                    'option': option, 'source_url': annotation['source_url'],
                                    'source_sha256': annotation['input_sha256'], 'page': annotation['page'],
                                    'source_text': match[0]})
            consumed.append(match.span())
        residue = text
        for start, end in sorted(consumed, reverse=True):
            residue = residue[:start] + ' ' * (end - start) + residue[end:]
        if re.search(r'Hlasovanie č\.', residue, re.I):
            unresolved.append({'date': day, 'page': annotation['page'], 'reason': 'unparsed correction instruction',
                               'text': residue.strip()})
    if unresolved:
        raise ValueError(json.dumps(unresolved, ensure_ascii=False, indent=2))

    revised = json.loads(json.dumps(extracted))
    revised_events = {event['id']: event for event in revised['events']}
    for correction in corrections:
        event = revised_events[correction['event_id']]
        row = next(r for r in event['rows'] if r['source_name'] == correction['source_name'])
        if row['option'] != correction['source_option']:
            raise ValueError(f"Source option changed for {event['id']} / {row['source_name']}")
        row['manual_correction'] = {k: correction[k] for k in
                                    ('source_option', 'option', 'source_url', 'source_sha256', 'page', 'source_text')}
        row['option'] = correction['option']
    cfg = json.loads((city / 'config/sources.json').read_text())
    for event in revised['events']:
        corrections_for_event = [c for c in corrections if c['event_id'] == event['id']]
        invalid_for_event = [c for c in invalid if c['event_id'] == event['id']]
        if corrections_for_event:
            counts = Counter(row['option'] for row in event['rows'])
            options = source_present_options(cfg, event['date'], event['id'])
            present = sum(counts[o] for o in options)
            if present != event['present_count']:
                event['present_count_basis'] = {
                    'published_present_count': event['present_count'],
                    'manual_corrections': len(corrections_for_event),
                    'adjusted_present_count': present,
                    'note': 'Adjusted using named manual votes in the cited correction appendix; original published aggregate remains in published_totals.'}
                event['present_count'] = present
            event['counts'] = {o: counts[o] for o in ('yes', 'no', 'abstain', 'not_voting', 'absent')}
            event['manual_corrections'] = len(corrections_for_event)
        if invalid_for_event:
            event['status'] = 'invalid'
            event['status_source'] = {k: invalid_for_event[0][k] for k in
                                      ('source_url', 'source_sha256', 'page', 'source_text')}
    correction_doc = {'city': 'kosice', 'review_status': 'reviewed',
                      'method': 'Names and requested options matched against extracted source rows; each appendix URL, original SHA-256, page, and instruction retained.',
                      'corrections': corrections, 'invalid_events': invalid}
    (city / 'source/corrections.json').write_text(json.dumps(correction_doc, ensure_ascii=False, indent=2) + '\n')
    (city / 'work/reviewed-extraction.json').write_text(json.dumps(revised, ensure_ascii=False, indent=2) + '\n')
    print(f"Reviewed {len(extracted['annotations'])} appendix pages: {len(corrections)} named overrides, {len(invalid)} invalid-event markings; all matched and tallies reconciled")


if __name__ == '__main__':
    review()
