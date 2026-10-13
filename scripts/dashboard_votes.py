"""Publish small, cacheable vote files; never assemble full histories in the web app."""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

MAX_BYTES = 1_000_000  # Leave room for Next.js cache serialization/base64 overhead.


def encode(value):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Dashboard artifact exceeds the cache size budget")
    return text


def build_dashboard_votes(tables):
    people = {p["id"]: p["name"] for p in tables["persons"]}
    group_ids = {o["id"] for o in tables["organizations"] if o["classification"] == "group"}
    groups = defaultdict(list)
    for membership in tables["memberships"]:
        if membership["organization_id"] in group_ids:
            groups[membership["person_id"]].append(membership)
    votes = defaultdict(list)
    for vote in tables["votes"]:
        if vote["voter_type"] == "person":
            votes[vote["vote_event_id"]].append(vote)
    events = sorted((e for e in tables["vote_events"] if e["status"] == "valid"),
                    key=lambda e: (e["start_date"], e["id"]), reverse=True)
    summaries, files = [], {}
    for event in events:
        city, file_id = event["id"].split(":vote-event:", 1)
        if not re.fullmatch(r"[A-Za-z0-9._-]+", file_id) or file_id in (".", ".."):
            raise ValueError(f"Unsafe vote event filename: {file_id}")
        counts = {c["option"]: c["value"] for c in event["counts"]}
        day = event["start_date"][:10]
        voters = []
        for vote in votes[event["id"]]:
            person_id = vote["voter_id"]
            membership = next((m for m in groups[person_id]
                               if m["start_date"] <= day and
                               (not m.get("end_date") or day < m["end_date"])), None)
            option = vote["option"]
            voters.append({"voter_id": person_id, "option": option,
                           "polarity": "support" if option == "yes" else "oppose" if option == "no" else "neutral",
                           "name": people.get(person_id, person_id),
                           "group_id": membership["organization_id"] if membership else None})
        extras = event.get("extras", {})
        support, oppose = counts.get("yes", 0), counts.get("no", 0)
        neutral = sum(counts.get(option, 0) for option in ("abstain", "absent", "not_voting"))
        summary = {"id": event["id"], "start_date": event["start_date"],
                   "title": extras.get("topic") or event.get("identifier") or event["id"],
                   "result": extras.get("result"),
                   "polarity_counts": {"support": support, "oppose": oppose, "neutral": neutral,
                                       "total": support + oppose + neutral},
                   "option_counts": {"abstain": counts.get("abstain", 0),
                                     "did_not_vote": counts.get("absent", 0) + counts.get("not_voting", 0)}}
        detail = {**summary, "parliament_id": city, "definition_name": None,
                  "votes": voters, "sources": event.get("sources", []), "extras": extras}
        for key in ("identifier", "requirement", "required_count"):
            if key in event:
                detail[key] = event[key]
        if "topic_description" in extras:
            detail["topic_description"] = extras["topic_description"]
        files[f"vote-events/{file_id}.json"] = encode(detail)
        summaries.append(summary)
    pages = []
    for start in range(0, len(summaries), 250):
        filename = f"summaries/{start // 250:04d}.json"
        files[filename] = encode(summaries[start:start + 250])
        pages.append(filename)
    files["index.json"] = encode({"version": 1, "count": len(summaries), "pages": pages})
    return files


def write_dashboard_votes(tables, out):
    # Construct and validate every artifact before updating the published directory.
    files = build_dashboard_votes(tables)
    for name, text in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
    # This directory is wholly generated; remove withdrawn events/obsolete shards.
    for target in out.rglob("*.json"):
        if target.relative_to(out).as_posix() not in files:
            target.unlink()


def read_tables(data):
    tables = {"vote_events": json.loads((data / "vote_events.json").read_text(encoding="utf-8"))}
    for name in ("persons", "organizations", "memberships", "votes"):
        with (data / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
            tables[name] = list(csv.DictReader(stream))
    return tables


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=("bratislava", "kosice"))
    args = parser.parse_args()
    data = Path(__file__).resolve().parents[1] / args.city / "data"
    write_dashboard_votes(read_tables(data), data / "dashboard")
    print(f"{args.city}: dashboard vote artifacts published")
