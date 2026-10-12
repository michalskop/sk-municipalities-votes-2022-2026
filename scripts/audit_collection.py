"""Record a compact, reproducible audit of collected originals and draft coverage."""
import hashlib
import json
from datetime import datetime, timezone

from scripts.standardize import ROOT


def audit():
    cities = {}
    for city in ('bratislava', 'kosice'):
        work = ROOT / city / 'work'
        inventory_path = work / 'sources/inventory.json'
        report_path = work / 'extraction-report.json'
        if not inventory_path.exists() or not report_path.exists():
            raise ValueError(f'Collect and extract {city} before auditing')
        inventory = json.loads(inventory_path.read_text())
        report = json.loads(report_path.read_text())
        if report.get('inventory_sha256') != hashlib.sha256(inventory_path.read_bytes()).hexdigest():
            raise ValueError(f'{city}: extraction report is stale; rerun extract_inventory')
        cfg = json.loads((ROOT / city / 'config/sources.json').read_text())
        receipt_by_url = {r['url']: r for r in inventory['downloads']}
        sources = []
        for meeting in inventory['meetings']:
            if city == 'bratislava':
                receipts = meeting.get('voting_sources', [])
            else:
                receipts = [receipt_by_url[d['url']] for d in meeting['documents'] if '/meeting/vote/' in d['url']]
            for receipt in receipts:
                path = work / 'sources' / receipt['file']
                if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
                    raise ValueError(f'Original source bytes changed: {receipt["url"]}')
                sources.append({k: receipt[k] for k in ('url', 'sha256', 'retrieved_at', 'view_context') if k in receipt})
        cities[city] = {'archive_url': cfg['archive_url'],
                        'inventory_sha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
                        'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
                        **report, 'voting_sources': sources}
    result = {'audited_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Original-source collection and draft extraction; identities, corrections, event status and full-term coverage still require review. No production publication approval.',
              'cities': cities}
    (ROOT / 'docs/source-collection-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for city, row in cities.items():
        print(f'{city}: {len(row["meetings"])} collected meetings, {row["named_events"]} named draft events, {len(row["errors"])} unresolved source errors')


if __name__ == '__main__':
    audit()
