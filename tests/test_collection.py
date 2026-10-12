"""Regression for a single URL serving different Bratislava tab contents."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.collect_sources import collect


class CollectionTests(unittest.TestCase):
    def test_program_and_vote_pagination_have_separate_receipts_and_resume(self):
        archive = 'https://zastupitelstvo.bratislava.sk/'
        meeting = archive + 'mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-04102023/'
        tab = meeting + '?rokovanie_tab_308066=2'
        page = meeting + '?page=1'
        calls = []

        class Session:
            headers = {}

            def __init__(self):
                self.voting = False

            def get(self, url, timeout):
                calls.append(url)
                if url == archive:
                    html = f'<a href="{meeting}">Meeting</a>'
                elif url == tab:
                    self.voting = True
                    html = '<div class="panel hlasovania">Hlasovanie číslo 1</div><a href="?page=1">Next</a>'
                elif url == page and self.voting:
                    html = '<div class="panel hlasovania">Hlasovanie číslo 16</div>'
                else:
                    html = '<a href="?rokovanie_tab_308066=2">Hlasovania</a><a href="?page=1">Next</a><p>Program</p>'

                class Response:
                    content = html.encode()
                    text = html

                    def raise_for_status(self):
                        pass

                return Response()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'bratislava/config'
            config.mkdir(parents=True)
            (config / 'sources.json').write_text(json.dumps({
                'archive_url': archive, 'meeting_pattern': r'^/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy-2022-2026-zasadnutie-\d{8}/$',
                'term_start': '2022-11-15'}))
            with patch('scripts.collect_sources.ROOT', root), patch('scripts.collect_sources.requests.Session', Session), patch('scripts.collect_sources.time.sleep'):
                collect('bratislava')
                work = root / 'bratislava/work/sources'
                receipts = json.loads((work / 'downloads.json').read_text())
                variants = [r for r in receipts if r['url'] == page]
                self.assertEqual(len(variants), 2)
                self.assertEqual({r.get('view_context') for r in variants}, {None, 'rokovanie_tab_308066=2'})
                inventory = json.loads((work / 'inventory.json').read_text())
                vote_page = next(r for r in inventory['meetings'][0]['voting_sources'] if r['url'] == page)
                self.assertIn('Hlasovanie číslo 16', (work / vote_page['file']).read_text())
                for r in receipts:
                    self.assertEqual(hashlib.sha256((work / r['file']).read_bytes()).hexdigest(), r['sha256'])
                calls.clear()
                collect('bratislava')
                # A fresh session still selects the tab; page bytes resume from
                # their context-specific cache without refetching program HTML.
                self.assertEqual(calls, [tab])


if __name__ == '__main__':
    unittest.main()
