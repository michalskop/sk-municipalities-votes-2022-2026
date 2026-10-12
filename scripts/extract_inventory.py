"""Extract collected originals and report every unresolved source explicitly.

This produces drafts, never reviewed inputs or published data. Failed documents,
secret ballots, annotations, and meetings without named votes remain visible.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from scripts.standardize import ROOT
from scripts.extract_bratislava import extract as extract_ba
from scripts.extract_kosice import extract as extract_ke


def agenda_key(url):
    path = re.sub(r'^/\d+-sk/', '/', urlparse(url).path)
    return path.replace('-2022-2026', '').rstrip('/')


def extract_inventory(city, meeting_date=None):
    work = ROOT / city / 'work'
    sources = work / 'sources'
    inventory_raw = (sources / 'inventory.json').read_bytes()
    inventory = json.loads(inventory_raw)
    receipts = {r['url']: r for r in json.loads((sources / 'downloads.json').read_text())}
    target = work / 'extracted.json'
    existing = json.loads(target.read_text()) if meeting_date and target.exists() else {}
    if meeting_date and not existing:
        raise ValueError('A date-scoped refresh requires an existing draft; run the full extraction first')
    events = {e['id']: e for e in existing.get('events', [])
              if e.get('meeting_url') not in {m['url'] for m in inventory['meetings'] if m['date'] == meeting_date}}
    errors = [e for e in existing.get('errors', [])
              if e.get('meeting_url') not in {m['url'] for m in inventory['meetings'] if m['date'] == meeting_date}]
    meeting_reports = {m['url']: m for m in existing.get('meetings', [])}
    replaced_sources = {d['url'] for m in inventory['meetings'] if m['date'] == meeting_date
                        for d in m.get('documents', [])}
    annotations = [a for a in existing.get('annotations', []) if a.get('source_url') not in replaced_sources]
    secret = [a for a in existing.get('secret_ballots', [])
              if a.get('meeting_url') not in {m['url'] for m in inventory['meetings'] if m['date'] == meeting_date}]
    for meeting in inventory['meetings']:
        if meeting_date and meeting['date'] != meeting_date:
            continue
        title_lookup = {agenda_key(url): title for url, title in meeting.get('agenda_titles', {}).items()}
        voting_receipts = {r['url']: r for r in meeting.get('voting_sources', [])}
        urls = (meeting.get('voting_urls', []) if city == 'bratislava' else
                [d['url'] for d in meeting['documents'] if '/meeting/vote/' in d['url']])
        found = set()
        for url in urls:
            receipt = voting_receipts.get(url) or receipts.get(url)
            try:
                if receipt is None:
                    raise ValueError('Source has no download receipt')
                path = sources / receipt['file']
                if city == 'bratislava':
                    try:
                        draft = extract_ba(path, url, meeting['date'])
                    except ValueError as exc:
                        if str(exc) != 'No named voting content in HTML':
                            raise
                        text = BeautifulSoup(path.read_bytes(), 'html.parser').get_text()
                        if 'Neboli nájdené žiadne záznamy' in text and not re.search(r'Hlasovanie číslo\s*\d', text):
                            continue
                        raise ValueError('Voting tab layout is unrecognized') from exc
                else:
                    draft = extract_ke(path, url)
                if draft['input_sha256'] != receipt['sha256']:
                    raise ValueError('Original bytes differ from their download receipt')
                for event in draft['events']:
                    event['sequence'] = event['source_vote_number']
                    if city == 'bratislava':
                        agenda = event.get('source_agenda_url')
                        title = title_lookup.get(agenda_key(agenda)) if agenda else None
                        if title:
                            event['title'] = title
                        elif not agenda:
                            event['title'] = event.get('source_note') or f"Procedurálne hlasovanie č. {event['source_vote_number']}"
                    if event['date'] < meeting['date']:
                        raise ValueError('Vote predates its meeting; inspect source date')
                    event['input_sha256'] = receipt['sha256']
                    event['meeting_url'] = meeting['url']
                    key = event['id']
                    if key in events:
                        # The same vote may be linked from multiple agenda items.
                        previous = events[key]
                        facts = ('rows', 'counts', 'date', 'source_vote_number')
                        if any(previous[k] != event[k] for k in facts):
                            raise ValueError(f'Conflicting duplicate vote: {key}')
                        previous['sources'].extend(s for s in event['sources'] if s not in previous['sources'])
                    else:
                        events[key] = event
                    found.add(key)
                annotations.extend({**a, 'source_url': url, 'input_sha256': receipt['sha256']}
                                   for a in draft.get('annotations', []))
                secret.extend({**a, 'source_url': url, 'input_sha256': receipt['sha256'], 'meeting_url': meeting['url']}
                              for a in draft.get('secret_ballots', []))
            except (ValueError, KeyError, OSError) as exc:
                errors.append({'meeting_url': meeting['url'], 'source_url': url, 'error': str(exc)})
        vote_numbers = sorted({events[key]['source_vote_number'] for key in found})
        missing = sorted(set(range(1, max(vote_numbers, default=0) + 1)) - set(vote_numbers))
        meeting_reports[meeting['url']] = {'url': meeting['url'], 'date': meeting['date'],
                         'source_documents': len(urls), 'named_events': len(found),
                         'named_vote_numbers': vote_numbers,
                         'missing_named_vote_numbers': missing,
                         'review_status': 'pending',
                         'needs_no_vote_evidence': not urls}
    meetings = sorted(meeting_reports.values(), key=lambda m: (m['date'], m['url']))
    result = {'city': city, 'review_status': 'draft', 'coverage_verified': False,
              'collection_complete': inventory.get('collection_complete', False),
              'limited_scan': inventory['limited_scan'],
              'discovered_meetings': len(inventory.get('discovered_meeting_urls', inventory['meetings'])),
              'meetings': meetings, 'errors': errors, 'annotations': annotations,
              'secret_ballots': secret,
              'events': sorted(events.values(), key=lambda e: (e['date'], e['id']))}
    work.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(target)
    summary = {k: result[k] for k in ('city', 'collection_complete', 'limited_scan', 'discovered_meetings', 'coverage_verified')}
    summary['inventory_sha256'] = hashlib.sha256(inventory_raw).hexdigest()
    summary.update(named_events=len(events), individual_votes=sum(len(e['rows']) for e in events.values()),
                   errors=errors, annotation_pages=len(annotations), secret_ballots=len(secret),
                   meetings=meetings)
    (work / 'extraction-report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(f'{city}: {len(events)} named events, {len(errors)} unresolved source errors; review pending')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('city', choices=['bratislava', 'kosice'])
    parser.add_argument('--meeting-date', help='Refresh one ISO date in an existing draft')
    args = parser.parse_args()
    extract_inventory(args.city, args.meeting_date)
