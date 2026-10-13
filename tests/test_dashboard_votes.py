"""Verify dashboard exports preserve ballots, historical clubs, and provenance."""
import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.dashboard_votes import MAX_BYTES, build_dashboard_votes, read_tables, write_dashboard_votes
from scripts.standardize import ROOT, transform
from test_pipeline import fixture


class DashboardVoteTests(unittest.TestCase):
    def test_historical_club_boundary_and_all_neutral_options(self):
        tables = transform("kosice", fixture(), clubs={})
        tables["organizations"] += [{"id": "old", "classification": "group"},
                                    {"id": "new", "classification": "group"}]
        tables["memberships"] += [
            {"person_id": "kosice:person:0", "organization_id": "old",
             "start_date": "2022-11-11", "end_date": "2025-12-12"},
            {"person_id": "kosice:person:0", "organization_id": "new", "start_date": "2025-12-12"},
        ]
        files = build_dashboard_votes(tables)
        event = json.loads(files["vote-events/2025-12-12-001.json"])
        self.assertEqual(event["votes"][0]["group_id"], "new")
        self.assertEqual(event["polarity_counts"], {"support": 1, "oppose": 1, "neutral": 3, "total": 5})
        self.assertEqual(event["option_counts"], {"abstain": 1, "did_not_vote": 2})
        self.assertEqual(event["sources"], tables["vote_events"][0]["sources"])

    def test_invalid_events_are_excluded_and_withdrawn_files_removed(self):
        tables = transform("kosice", fixture(), clubs={})
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            write_dashboard_votes(tables, out)
            tables["vote_events"][0]["status"] = "invalid"
            write_dashboard_votes(tables, out)
            self.assertFalse(list((out / "vote-events").glob("*.json")))
            self.assertFalse(list((out / "summaries").glob("*.json")))
            self.assertEqual(json.loads((out / "index.json").read_text())["count"], 0)

    def test_bad_filename_and_oversize_artifact_rejected(self):
        tables = transform("kosice", fixture(), clubs={})
        unsafe = copy.deepcopy(tables)
        unsafe["vote_events"][0]["id"] = "kosice:vote-event:../escape"
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            build_dashboard_votes(unsafe)
        tables["vote_events"][0]["extras"]["topic"] = "x" * MAX_BYTES
        with self.assertRaisesRegex(ValueError, "cache size"):
            build_dashboard_votes(tables)

    def test_every_production_ballot_and_summary_matches_standard_tables(self):
        for city in ("bratislava", "kosice"):
            with self.subTest(city=city):
                tables = read_tables(ROOT / city / "data")
                files = build_dashboard_votes(tables)
                index = json.loads(files["index.json"])
                summaries = [s for name in index["pages"] for s in json.loads(files[name])]
                valid = {e["id"]: e for e in tables["vote_events"] if e["status"] == "valid"}
                self.assertEqual({s["id"] for s in summaries}, set(valid))
                self.assertEqual(index["count"], len(valid))
                actual = Counter()
                expected = Counter((v["vote_event_id"], v["voter_id"], v["option"])
                                   for v in tables["votes"] if v["vote_event_id"] in valid)
                for summary in summaries:
                    event = valid[summary["id"]]
                    detail = json.loads(files[f"vote-events/{event['id'].split(':vote-event:')[1]}.json"])
                    actual.update((detail["id"], v["voter_id"], v["option"]) for v in detail["votes"])
                    counts = Counter(v["polarity"] for v in detail["votes"])
                    self.assertEqual(detail["polarity_counts"], {"support": counts["support"],
                        "oppose": counts["oppose"], "neutral": counts["neutral"], "total": len(detail["votes"])})
                    self.assertEqual(detail["sources"], event["sources"])
                    self.assertEqual(detail["extras"], event["extras"])
                    self.assertNotIn("votes", summary)
                self.assertEqual(actual, expected)
                self.assertTrue(all(len(text.encode()) <= MAX_BYTES for text in files.values()))
