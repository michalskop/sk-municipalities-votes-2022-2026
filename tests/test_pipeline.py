"""Synthetic fixtures verify gates; these are not municipal production data."""
import copy
import tempfile
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.collect_sources import document_links, meeting_links
from scripts.standardize import ROOT, DEFAULT_SCHEMAS, OPTIONS, transform, validate, write_tables


def fixture(city="kosice"):
    sources = [{"url": "https://example.org/synthetic-test-only"}]
    members = [{"id": f"{city}:person:{i}", "name": f"Person {i}",
                "given_name": "Person", "family_name": str(i), "sources": sources,
                "mandates": [{"since": "2022-11-11", "sources": sources}]}
               for i in range(5)]
    return {"city": city, "review_status": "reviewed", "members": members,
            "events": [{"id": "2025-12-12-001", "date": "2025-12-12",
                        "title": "Synthetic test motion", "status": "valid", "sources": sources,
                        "present_count": 3 if city == "kosice" else 4,
                        "counts": {option: 1 for option in OPTIONS},
                        "votes": [{"person_id": m["id"], "option": option}
                                  for m, option in zip(members, OPTIONS)]}]}


class PipelineTests(unittest.TestCase):
    def test_same_day_oath_excludes_only_votes_before_its_reviewed_event(self):
        data = fixture()
        first = data['events'][0]
        first['sequence'] = 1
        second = copy.deepcopy(first)
        second['id'] = '2025-12-12-002'
        second['sequence'] = 2
        data['events'].append(second)
        period = data['members'][0]['mandates'][0]
        period.update(since=first['date'], since_event=second['id'])
        first['votes'].pop(0)
        first['counts']['yes'] = 0
        first['present_count'] -= 1
        tables = transform('kosice', data)
        validate(tables, DEFAULT_SCHEMAS)
        rows = [v for v in tables['votes'] if v['voter_id'] == data['members'][0]['id']]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['vote_event_id'].endswith(second['id']))

    def test_event_scoped_mandate_requires_reviewed_event_order(self):
        data = fixture()
        data['members'][0]['mandates'][0].update(since='2025-12-12', since_event='2025-12-12-001')
        with self.assertRaisesRegex(ValueError, 'reviewed sequence'):
            transform('kosice', data)
        data['events'][0]['sequence'] = 1
        data['members'][0]['mandates'][0]['since_event'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'included event'):
            transform('kosice', data)

    def test_same_day_mandate_end_includes_boundary_event_only(self):
        data = fixture()
        first = data['events'][0]
        first['sequence'] = 1
        second = copy.deepcopy(first)
        second.update(id='2025-12-12-002', sequence=2)
        data['events'].append(second)
        data['members'][0]['mandates'][0].update(until=first['date'], until_event=first['id'])
        second['votes'].pop(0)
        second['counts']['yes'] = 0
        second['present_count'] -= 1
        tables = transform('kosice', data)
        validate(tables, DEFAULT_SCHEMAS)
        self.assertEqual(len([v for v in tables['votes'] if v['voter_id'] == data['members'][0]['id']]), 1)

    def test_both_cities_validate_against_shared_schemas(self):
        for city in ("bratislava", "kosice"):
            tables = transform(city, fixture(city))
            validate(tables, DEFAULT_SCHEMAS)
            with tempfile.TemporaryDirectory() as temp:
                write_tables(tables, Path(temp))
                self.assertEqual(len(list(Path(temp).iterdir())), 7)

    def test_missing_member_is_not_silently_absent(self):
        data = fixture()
        data["events"][0]["votes"].pop()
        with self.assertRaisesRegex(ValueError, "Roster mismatch"):
            transform("kosice", data)

    def test_duplicate_vote_rejected(self):
        data = fixture()
        data["events"][0]["votes"].append(data["events"][0]["votes"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate voter"):
            transform("kosice", data)

    def test_bad_tally_rejected(self):
        data = fixture()
        data["events"][0]["counts"]["yes"] = 4
        with self.assertRaisesRegex(ValueError, "Source tally mismatch"):
            transform("kosice", data)

    def test_present_nonvoting_is_distinct_from_absence(self):
        tables = transform("kosice", fixture())
        self.assertEqual(tables["vote_events"][0]["extras"]["source_present_count"], 3)
        self.assertEqual({v["option"] for v in tables["votes"]}, set(OPTIONS))

    def test_unknown_option_rejected(self):
        data = fixture()
        data["events"][0]["votes"][0]["option"] = "unknown"
        with self.assertRaisesRegex(ValueError, "Unknown vote option"):
            transform("kosice", data)

    def test_mandate_boundary_inclusive(self):
        data = fixture()
        data["members"][0]["mandates"][0]["until"] = "2025-12-12"
        transform("kosice", data)
        data["members"][0]["mandates"][0]["until"] = "2025-12-11"
        with self.assertRaisesRegex(ValueError, "Roster mismatch"):
            transform("kosice", data)

    def test_unreviewed_data_rejected(self):
        data = fixture()
        data["review_status"] = "draft"
        with self.assertRaisesRegex(ValueError, "marked reviewed"):
            transform("kosice", data)

    def test_overlapping_mandates_rejected(self):
        data = fixture()
        data["members"][0]["mandates"].append(copy.deepcopy(data["members"][0]["mandates"][0]))
        with self.assertRaisesRegex(ValueError, "overlapping mandates"):
            transform("kosice", data)

    def test_discovery_excludes_city_districts_and_other_terms(self):
        base = "https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026"
        pattern = r"^/mesto/samosprava/mestske-zastupitelstvo/2022-2026/zasadnutie/\d+/?$"
        html = '<a href="' + base + '/zasadnutie/1">Opening</a>'
        html += '<a href="/mesto/samosprava/mestske-zastupitelstvo/2018-2022/zasadnutie/1">Old</a>'
        self.assertEqual(meeting_links(html, base, pattern), [base + "/zasadnutie/1"])

    def test_split_vote_pdfs_are_all_retained(self):
        html = '<a href="/1.pdf">Hlasovanie č. 1-20</a><a href="/2.pdf">Hlasovanie č. 21-29</a>'
        html += '<a href="/meeting/memorandum/a/minutes.pdf">PDF</a><a href="/budget.pdf">Rozpočet</a>'
        self.assertEqual(len(document_links(html, "https://www.kosice.sk")), 3)

    def test_shared_attendance_engine_integration(self):
        with tempfile.TemporaryDirectory(prefix="sk-votes-test-") as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / "kosice/config", root / "kosice/config")
            (root / "kosice/source").mkdir()
            (root / "kosice/source/reviewed.json").write_text(json.dumps(fixture()))
            subprocess.run([sys.executable, "-m", "scripts.run_attendance", "kosice"],
                           cwd=root, check=True, capture_output=True, text=True)
            result = json.loads((root / "kosice/analyses/attendance/outputs/attendance.json").read_text())
            self.assertEqual(sum(r["present"] for r in result), 3)
            self.assertEqual(sum(r["absent"] for r in result), 2)


if __name__ == "__main__":
    unittest.main()
