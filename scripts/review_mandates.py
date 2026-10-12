"""Build sourced mandate periods while leaving identity review explicit."""
import json
from pathlib import Path

from scripts.standardize import ROOT


BA_ROSTER = 'https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026/'
BA_INITIAL = 'https://zastupitelstvo.bratislava.sk/297353-sk/uznesenia/uznesenie/'
BA_OATH_2022 = 'https://zastupitelstvo.bratislava.sk/data/att/65270.pdf'
BA_OATH_2024_SKAPIK = 'https://zastupitelstvo.bratislava.sk/data/att/71788.pdf'
BA_OATH_2024_ELENA = 'https://zastupitelstvo.bratislava.sk/data/att/72718.pdf'
BA_RES_SKAPIK = 'https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-29022024/bod-1/'
BA_RES_ELENA = 'https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-25042024/bod-1/'
BA_PROFILE = 'https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026/'
KE_ROSTER = 'https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/poslanci'
KE_OPENING = 'https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026/zasadnutie/1'


def sources(*urls):
    return [{'url': url} for url in urls]


def build(city):
    identity = json.loads((ROOT / city / 'source/identity-draft.json').read_text())
    records = []
    if city == 'bratislava':
        delayed = {'bratislava:person:145451', 'bratislava:person:212918'}
        special = {
            'bratislava:person:297333': {
                'until': '2023-12-14',
                'sources': sources(BA_ROSTER),
                'note': 'The official roster records resignation effective 15 December 2023; 14 December is the last day before that effective date.'},
            'bratislava:person:313925': {
                'since': '2024-02-29', 'since_event': '2024-02-29-001',
                'sources': sources(BA_OATH_2024_SKAPIK, BA_RES_SKAPIK),
                'note': 'The minutes record the oath before all roll-call votes; the first roll-call is the inclusive boundary.'},
            'bratislava:person:215312': {
                'until': '2024-04-14',
                'sources': sources(BA_RES_ELENA),
                'note': 'Resolution 477/2024 records resignation effective 15 April 2024; 14 April is the last day before that effective date.'},
            'bratislava:person:slug-patoprsta-smatana-elena': {
                'since': '2024-04-25', 'since_event': '2024-04-25-001',
                'sources': sources(BA_OATH_2024_ELENA, BA_RES_ELENA),
                'note': 'The minutes record the oath before all roll-call votes. Vote 1 records her absent; she is still an active member for that event.'},
        }
        for member in identity['members']:
            period = {'since': '2022-11-15', 'sources': sources(BA_INITIAL, BA_OATH_2022, member['sources'][0]['url'])}
            if member['id'] in delayed:
                period = {'since': '2022-11-29', 'since_event': '2022-11-29-007',
                          'sources': sources(BA_OATH_2022, member['sources'][0]['url']),
                          'note': 'The minutes place this oath before vote 7; votes 1–6 contain 43 sworn members and vote 7 contains all 45.'}
            if member['id'] in special:
                item = special[member['id']]
                if 'since' in item:
                    period.update({'since': item['since'], 'sources': item['sources'], 'note': item['note']})
                    if item.get('since_event'):
                        period['since_event'] = item['since_event']
                else:
                    period['until'] = item['until']
                    period['sources'].extend(item['sources'])
                    period['note'] = item['note']
            if member['id'] in ('bratislava:person:145451', 'bratislava:person:212918'):
                period['since'] = '2022-11-29'
                period['sources'] = sources(BA_OATH_2022, member['sources'][0]['url'])
            records.append({'person_id': member['id'], 'name': member['name'], 'periods': [period]})
        method = 'Membership starts are based on oath minutes. Delayed oaths and replacement oaths are ordered against numbered roll-call events; resignations use the official effective date, represented as the prior inclusive service day.'
        sources_all = sources(BA_ROSTER, BA_INITIAL, BA_OATH_2022, BA_OATH_2024_SKAPIK,
                              BA_RES_SKAPIK, BA_OATH_2024_ELENA, BA_RES_ELENA)
    else:
        for member in identity['members']:
            records.append({'person_id': member['id'], 'name': member['name'],
                            'periods': [{'since': '2022-11-11', 'sources': sources(KE_ROSTER, KE_OPENING),
                                         'note': 'The official roster IDs match all 41 rows in the opening named roll calls.'}]})
        method = 'All 41 official roster IDs are present in the opening sitting on 11 November 2022 and in the full-period named event rows; no council mandate replacement was found in the checked official sources.'
        sources_all = sources(KE_ROSTER, KE_OPENING)

    expected = 47 if city == 'bratislava' else 41
    if len(records) != expected or len({r['person_id'] for r in records}) != expected:
        raise ValueError(f'{city}: identity registry changed; expected {expected} unique source IDs')
    output = {'city': city, 'review_status': 'reviewed', 'identity_review_status': 'pending',
              'mandate_review_status': 'reviewed', 'checked_on': '2026-10-11',
              'method': method, 'sources': sources_all, 'members': records}
    target = ROOT / city / 'source/mandates.json'
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(f'{city}: recorded sourced mandate periods for {len(records)} identity-draft members; identity mapping remains pending')


if __name__ == '__main__':
    for municipality in ('bratislava', 'kosice'):
        build(municipality)
