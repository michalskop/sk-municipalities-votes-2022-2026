"""Convert reviewed municipal roll calls to the existing legislature data contract.

Input is source/reviewed.json, not unverified PDF extraction. See docs/input-format.md.
"""
import argparse
import csv
import json
import re
import tempfile
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = ("yes", "no", "abstain", "not_voting", "absent")
DEFAULT_SCHEMAS = Path("/home/michal/project/legislature-data/legislature-data-standard/dist")


def source_present_options(cfg, day, event_id=None):
    by_event = cfg.get('source_present_options_by_event', {}).get(event_id, {}) if event_id else {}
    return by_event.get('options', cfg.get('source_present_options_by_date', {}).get(day, {}).get('options',
        cfg.get('source_present_options', ['yes', 'no', 'abstain', 'not_voting'])))


def active(member, day, event_id=None, event_order=None):
    for period in member['mandates']:
        if not (period['since'] <= day and (not period.get('until') or day <= period['until'])):
            continue
        for field, boundary_day, before in (('since_event', period['since'], True),
                                            ('until_event', period.get('until'), False)):
            boundary = period.get(field)
            if boundary and day == boundary_day:
                if event_id is None or event_order is None:
                    raise ValueError('Event context required for an event-scoped mandate')
                if (before and event_order[event_id] < event_order[boundary]) or (not before and event_order[event_id] > event_order[boundary]):
                    break
        else:
            return True
    return False


def require_source(value):
    sources = value.get("sources", [])
    if not sources or any(not s.get("url", "").startswith("https://") for s in sources):
        raise ValueError("Every member, mandate, and event needs an HTTPS source URL")
    return sources


@lru_cache(maxsize=32)
def schema_validator(path):
    if not path.is_file():
        raise FileNotFoundError(f"Build the shared data standard first: missing {path}")
    return jsonschema.Draft7Validator(json.loads(path.read_text()))


def validate_schema(records, schemas, relative):
    schema_validator(schemas / relative).validate(records)


def transform(city, source):
    if source.get("city") != city or source.get("review_status") != "reviewed":
        raise ValueError("Input must identify the city and be marked reviewed")
    if not source.get("members") or not source.get("events"):
        raise ValueError("Members and events must both be nonempty")
    cfg = json.loads((ROOT / city / "config/sources.json").read_text())
    boundary_days = {p['since'] if field == 'since_event' else p.get('until')
                     for m in source['members'] for p in m.get('mandates', [])
                     for field in ('since_event', 'until_event') if p.get(field)}
    for day in boundary_days:
        same_day = [e for e in source['events'] if e['date'] == day]
        sequences = [e.get('sequence') for e in same_day]
        if any(type(n) is not int or n < 1 for n in sequences) or len(set(sequences)) != len(sequences):
            raise ValueError('Event-scoped mandates require unique positive reviewed sequence numbers for that date')
    ordered_events = sorted(source['events'], key=lambda e: (e['date'], e.get('sequence', 0), e['id']))
    event_order = {event['id']: i for i, event in enumerate(ordered_events)}
    event_dates = {event['id']: event['date'] for event in ordered_events}
    org_id = f"{city}:org:assembly"
    persons, memberships, all_members = [], [], []
    people = {}
    for member in sorted(source["members"], key=lambda m: m["id"]):
        pid = member["id"]
        if not re.fullmatch(rf"{city}:person:[A-Za-z0-9._-]+", pid) or pid in people:
            raise ValueError(f"Duplicate or wrongly scoped person ID: {pid}")
        if not member.get("name") or not member.get("mandates"):
            raise ValueError(f"Missing canonical name or mandate: {pid}")
        people[pid] = member
        person = {k: member[k] for k in ("id", "name", "given_name", "family_name")}
        person["sources"] = require_source(member)
        persons.append(person)
        periods = sorted(member["mandates"], key=lambda p: p["since"])
        previous_end = ""
        intervals = []
        for i, period in enumerate(periods):
            start, end = period["since"], period.get("until")
            date.fromisoformat(start)
            if end:
                date.fromisoformat(end)
            for field, boundary_day in (('since_event', start), ('until_event', end)):
                if period.get(field) and (not boundary_day or event_dates.get(period[field]) != boundary_day):
                    raise ValueError(f'{field} must reference an included event on its mandate boundary date: {pid}')
            if (end and end < start) or (i and (previous_end is None or previous_end >= start)):
                raise ValueError(f"Invalid or overlapping mandates: {pid}")
            previous_end = end
            memberships.append({"id": f"{city}:membership:{pid.rsplit(':', 1)[-1]}:{i}",
                                "person_id": pid, "organization_id": org_id,
                                "start_date": start, **({"end_date": end} if end else {}),
                                "sources": require_source(period)})
            boundaries = {key: f'{city}:vote-event:{period[key]}' for key in ('since_event', 'until_event') if period.get(key)}
            if boundaries:
                memberships[-1]['extras'] = {'event_boundaries': boundaries,
                                             'boundary_precision': 'official event order, not an invented timestamp'}
            intervals.append({"id": org_id, "name": cfg["name"],
                              "start_date": start, "end_date": end})
        all_members.append({**person, "memberships": {"parliament": intervals,
                            "groups": [], "candidate_list": [], "constituency": []}})
    organizations = [{"id": org_id, "name": cfg["name"], "classification": "assembly",
                      "sources": [{"url": cfg["archive_url"]}]}]
    events, motions, votes, seen = [], [], [], set()
    for event in ordered_events:
        key, day = event["id"], event["date"]
        date.fromisoformat(day)
        if not re.fullmatch(r"[A-Za-z0-9._-]+", key) or key in seen:
            raise ValueError(f"Duplicate or empty event ID: {key}")
        if day < (cfg.get("term_start") or "2022-11-01") or day >= "2027-01-01":
            raise ValueError(f"Event outside the target council term: {key}")
        seen.add(key)
        ballot = event["votes"]
        if len({v["person_id"] for v in ballot}) != len(ballot):
            raise ValueError(f"Duplicate voter in {key}")
        expected_people = {pid for pid, m in people.items() if active(m, day, key, event_order)}
        actual_people = {v["person_id"] for v in ballot}
        if actual_people != expected_people:
            raise ValueError(f"Roster mismatch for {key}: missing {expected_people - actual_people}, "
                             f"unexpected {actual_people - expected_people}")
        counts = Counter(v["option"] for v in ballot)
        if set(counts) - set(OPTIONS):
            raise ValueError(f"Unknown vote option in {key}")
        reported = event["counts"]
        if set(reported) != set(OPTIONS) or any(type(v) is not int or v < 0 for v in reported.values()):
            raise ValueError(f"All five reviewed integer counts required for {key}")
        if reported != {o: counts[o] for o in OPTIONS}:
            raise ValueError(f"Source tally mismatch for {key}")
        present_options = source_present_options(cfg, day, key)
        present = sum(counts[o] for o in present_options)
        if type(event["present_count"]) is not int or event["present_count"] != present:
            raise ValueError(f"Presence tally mismatch for {key}")
        if event.get("status") not in ("valid", "invalid", "test", "other"):
            raise ValueError(f"Explicit reviewed event status required for {key}")
        if not event.get("title"):
            raise ValueError(f"Missing motion title for {key}")
        sources = require_source(event)
        event_id, motion_id = f"{city}:vote-event:{key}", f"{city}:motion:{key}"
        events.append({"id": event_id, "identifier": key, "organization_id": org_id,
                       "motion_id": motion_id, "start_date": day, "status": event["status"],
                       "counts": [{"option": o, "value": counts[o]} for o in OPTIONS],
                       "sources": sources, "extras": {**event.get("extras", {}),
                       "source_present_count": present, "topic": event["title"], "date_precision": "day"}})
        if event.get('sequence') is not None:
            events[-1]['extras']['source_sequence'] = event['sequence']
        motions.append({"id": motion_id, "organization_id": org_id, "date": day,
                        "text": event["title"], "sources": sources})
        votes.extend({"vote_event_id": event_id, "voter_id": v["person_id"],
                      "voter_type": "person", "option": v["option"]}
                     for v in sorted(ballot, key=lambda v: v["person_id"]))
    return {"persons": persons, "organizations": organizations, "memberships": memberships,
            "votes": votes, "vote_events": events, "motions": motions, "all_members": all_members}


def validate(tables, schemas):
    for name in ("persons", "organizations", "memberships", "motions"):
        validate_schema(tables[name], schemas, f"dt/latest/schemas/{name}.dt.json")
    validate_schema(tables["vote_events"], schemas, "dt/latest/schemas/vote-events.dt.json")
    for row in tables["votes"]:
        validate_schema(row, schemas, "dt/latest/schemas/votes-table.dt.json")
    validate_schema(tables["all_members"], schemas,
                    "dt.analyses/all-members/latest/schemas/all-members.dt.analyses.json")


def write_tables(tables, out):
    out.mkdir(parents=True, exist_ok=True)
    for name in ("persons", "organizations", "memberships", "votes"):
        fields = sorted({key for row in tables[name] for key in row})
        with (out / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows({key: json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict))
                             else val for key, val in row.items()} for row in tables[name])
    for name in ("vote_events", "motions"):
        (out / f"{name}.json").write_text(json.dumps(tables[name], ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=["bratislava", "kosice"])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    args = parser.parse_args()
    city_root = ROOT / args.city
    source = json.loads((args.input or city_root / "source/reviewed.json").read_text())
    tables = transform(args.city, source)
    validate(tables, args.schemas)
    # All quality gates run before touching the existing published tables.
    with tempfile.TemporaryDirectory(dir=city_root) as temp:
        write_tables(tables, Path(temp))
        target = city_root / "data"
        target.mkdir(exist_ok=True)
        for file in Path(temp).iterdir():
            file.replace(target / file.name)
    work = city_root / "work/analysis_inputs"
    work.mkdir(parents=True, exist_ok=True)
    (work / "all_members.json").write_text(json.dumps(tables["all_members"], ensure_ascii=False, indent=2) + "\n")
    print(f"{args.city}: validated {len(tables['vote_events'])} events and {len(tables['votes'])} votes")
