"""Regression tests against saved official roll-call facts, not invented votes."""
import json
import unittest

from scripts.extract_bratislava import extract as extract_ba, parse_vote_text
from scripts.extract_kosice import extract as extract_ke, parse_page
from scripts.standardize import ROOT, source_present_options
from scripts.collect_sources import agenda_links, detail_page_links

KE_OPENING = ROOT / "kosice/source/extracts/2022-11-11-votes-21-29.json"
KE_LATER = ROOT / "kosice/source/extracts/2025-02-27-vote-49.json"
KE_MANUAL = ROOT / "tests/fixtures/kosice-manual-matrix.pdf"
BA_VOTE = ROOT / "bratislava/source/extracts/2023-12-14-vote-32.json"


class SourceAdapterTests(unittest.TestCase):
    def test_original_bratislava_panels_preserve_ids_and_ignore_page_footer(self):
        result = extract_ba(ROOT / 'tests/fixtures/bratislava-vote.html',
                            'https://zastupitelstvo.bratislava.sk/example/', '2023-12-14')
        event = result['events'][0]
        self.assertEqual(event['counts'], extract_ba(BA_VOTE)['events'][0]['counts'])
        self.assertEqual(len({r['source_person_id'] for r in event['rows']}), 45)
        self.assertEqual(event['source_resolution'], '414/2023')

    def test_embedded_font_maps_recover_original_names_and_blank_absent_cards(self):
        result = extract_ke(ROOT / 'tests/fixtures/kosice-encoded.pdf', 'https://static.kosice.sk/example.pdf')
        self.assertTrue(result['recovered_fonts'])
        first, later = result['events']
        self.assertEqual(first['rows'][0]['source_name'], 'Iveta Adamčíková')
        self.assertEqual(first['counts']['yes'], 36)
        self.assertEqual(first['rows'][15]['source_card'], None)
        self.assertEqual(later['source_vote_number'], 8)
        self.assertEqual(later['present_count'], sum(later['counts'][o] for o in ('yes', 'no', 'abstain', 'not_voting')))

    def test_original_secret_ballot_never_creates_individual_votes(self):
        result = extract_ke(ROOT / 'tests/fixtures/kosice-secret.pdf', 'https://static.kosice.sk/example.pdf')
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['secret_ballots'][0]['source_vote_number'], 14)
        self.assertEqual(result['secret_ballots'][0]['published_totals']['yes'], 19)

    def test_original_correction_appendix_remains_pending_review(self):
        result = extract_ke(ROOT / 'tests/fixtures/kosice-correction.pdf', 'https://static.kosice.sk/example.pdf')
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['annotations'][0]['page'], 2)
        self.assertIn('ZMÄTOČNÉ', result['annotations'][0]['text'])
        self.assertEqual(result['annotations'][0]['review_status'], 'pending')

    def test_manual_matrix_reconciles_attendance_check_and_five_unanimous_votes(self):
        url = "https://static.kosice.sk/meeting/vote/aiB2tgHd5bt16ee/LDuzd9FBWKfuOQB/vtqNCVyqyDhIulTdh/hlasovanie281024_1_6_rucne.pdf"
        result = extract_ke(KE_MANUAL, url)
        self.assertEqual(len(result["events"]), 6)
        check, *votes = result["events"]
        self.assertEqual(check["status"], "test")
        self.assertEqual(check["counts"], {"yes": 0, "no": 0, "abstain": 0, "not_voting": 37, "absent": 4})
        self.assertEqual(check["present_count"], 37)
        config = json.loads((ROOT / "kosice/config/sources.json").read_text())
        self.assertEqual(source_present_options(config, check["date"], check["id"]), ["not_voting"])
        self.assertTrue(all(v["counts"] == {"yes": 37, "no": 0, "abstain": 0, "not_voting": 0, "absent": 4} for v in votes))
        self.assertTrue(all(len(event["rows"]) == 41 for event in result["events"]))

    def test_agenda_voting_tab_preserves_its_observed_item_identifier(self):
        from scripts.collect_sources import agenda_voting_links
        url = 'https://zastupitelstvo.bratislava.sk/meeting/bod-20/'
        html = '<a href="?bod-typ-312040=hlasovania">Hlasovanie</a><a href="?bod-typ-312040=uznesenia">Other</a>'
        self.assertEqual(agenda_voting_links(html, url), [url + '?bod-typ-312040=hlasovania'])

    def test_meeting_vote_pagination_carries_explicit_view_context(self):
        from scripts.collect_sources import voting_page_links
        base = 'https://zastupitelstvo.bratislava.sk/meeting/'
        html = '<a href="?page=1">Next</a><a href="/other/?page=1">Other</a>'
        self.assertEqual(voting_page_links(html, base + '?rokovanie_tab_308066=2'),
                         [base + '?page=1'])

    def test_bratislava_discovery_keeps_items_pagination_and_tabs(self):
        url = "https://zastupitelstvo.bratislava.sk/meeting/"
        html = '<a href="bod-20/">Item</a><a href="?page=2">Next</a>'
        html += '<a href="?rokovanie_tab_345735=2">Hlasovania</a><a href="/other/bod-1/">Other</a>'
        self.assertEqual(agenda_links(html, url), [url + "bod-20/"])
        self.assertEqual(detail_page_links(html, url), [url + "?page=2", url + "?rokovanie_tab_345735=2"])

    def test_older_bratislava_agenda_slug_can_omit_term_but_not_change_date(self):
        base = 'https://zastupitelstvo.bratislava.sk/mestske-zastupitelstvo-hlavneho-mesta-sr-bratislavy'
        meeting = base + '-2022-2026-zasadnutie-29112022/'
        old = base + '-zasadnutie-29112022/bod-1/'
        other = base + '-zasadnutie-15112022/bod-1/'
        self.assertEqual(agenda_links(f'<a href="{old}">Oath</a><a href="{other}">Other</a>', meeting), [old])

    def test_kosice_opening_document_has_all_nine_events(self):
        result = extract_ke(KE_OPENING)
        self.assertEqual(result["review_status"], "draft")
        self.assertEqual([e["source_vote_number"] for e in result["events"]], list(range(21, 30)))
        self.assertTrue(all(len(e["rows"]) == 41 for e in result["events"]))
        first = result["events"][0]
        self.assertEqual(first["counts"], {"yes": 36, "no": 0, "abstain": 3, "not_voting": 2, "absent": 0})
        self.assertEqual(first["published_totals"]["missing"], 2)
        self.assertEqual(first["present_count"], 39)
        self.assertEqual(first["source_time"], "13:34")
        self.assertEqual([r["source_row"] for r in first["rows"] if r["option"] == "not_voting"], [11, 34])

    def test_kosice_later_source_preserves_clubs_and_zero_cards(self):
        event = extract_ke(KE_LATER)["events"][0]
        self.assertEqual(event["counts"], {"yes": 31, "no": 0, "abstain": 0, "not_voting": 4, "absent": 6})
        self.assertEqual(event["present_count"], 31)
        self.assertEqual(event["rows"][0]["source_group"], "Košický klub")
        self.assertEqual(event["rows"][1]["source_group"], "Starostovia a nezávislí kandidáti")
        self.assertEqual(event["sources"][0]["note"], "PDF page 9")
        self.assertTrue(all(r["source_card"] == 0 for r in event["rows"] if r["option"] == "absent"))

    def test_bratislava_all_five_lists_reconcile(self):
        event = extract_ba(BA_VOTE)["events"][0]
        self.assertEqual(event["source_vote_number"], 32)
        self.assertEqual(event["source_resolution"], "414/2023")
        self.assertEqual(len(event["rows"]), 45)
        self.assertEqual(event["counts"], {"yes": 29, "no": 0, "abstain": 0, "not_voting": 3, "absent": 13})
        self.assertEqual(event["present_count"], 32)
        self.assertEqual(event["rows"][0]["source_name"], "Mgr. Antalová Plavuchová Lenka")

    def test_missing_bratislava_name_fails(self):
        source = json.loads(BA_VOTE.read_text())
        text = source["text"].replace("  * Mgr. art. Berka Adam\n", "")
        with self.assertRaisesRegex(ValueError, "published 29, extracted 28"):
            parse_vote_text(text, source["date"], source["url"], source["title"])

    def test_bratislava_previous_council_term_rejected(self):
        source = json.loads(BA_VOTE.read_text())
        with self.assertRaisesRegex(ValueError, "Wrong council term"):
            parse_vote_text(source["text"], "2022-11-14", source["url"], source["title"])

    def test_missing_zero_count_list_fails(self):
        source = json.loads(BA_VOTE.read_text())
        text = source["text"].replace("Hlasovali proti: 0", "")
        with self.assertRaisesRegex(ValueError, "all five"):
            parse_vote_text(text, source["date"], source["url"], source["title"])

    def test_unknown_kosice_option_fails(self):
        source = json.loads(KE_OPENING.read_text())
        page = source["pages"][0].replace("Iveta Adamčíková ZA", "Iveta Adamčíková UNKNOWN")
        with self.assertRaisesRegex(ValueError, "unknown or wrapped"):
            parse_page(page, source["url"], 1)

    def test_changed_kosice_aggregate_fails(self):
        source = json.loads(KE_OPENING.read_text())
        page = source["pages"][0].replace("ZA HLASOVALO: 36", "ZA HLASOVALO: 35")
        with self.assertRaisesRegex(ValueError, "disagree with published"):
            parse_page(page, source["url"], 1)

    def test_kosice_cast_votes_are_distinct_from_registered_cards(self):
        source = json.loads(KE_OPENING.read_text())
        page = source["pages"][0].replace("POČET PRÍTOMNÝCH: 39", "POČET PRÍTOMNÝCH: 41")
        with self.assertRaisesRegex(ValueError, "present total disagrees"):
            parse_page(page, source["url"], 1)

    def test_bratislava_html_option_blocks(self):
        # Synthetic HTML tests the parser boundary; actual downloaded HTML is
        # still needed for a full DOM regression sample.
        import tempfile
        from pathlib import Path
        html = '<html><title>Example</title><body><h3>Hlasovanie číslo 1</h3>'
        for label in ("Hlasovali za", "Hlasovali proti", "Zdržali sa hlasovania", "Nehlasovali", "Neprítomní"):
            html += f'<p>{label}: <span>{1 if label == "Hlasovali za" else 0}</span></p>'
            html += '<ul><li>Person Example</li></ul>' if label == "Hlasovali za" else '<p>Neboli nájdené žiadne záznamy</p>'
        html += '</body></html>'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(html)
            event = extract_ba(path, "https://example.org/vote", "2023-12-14")["events"][0]
            self.assertEqual(len(event["rows"]), 1)


if __name__ == "__main__":
    unittest.main()
