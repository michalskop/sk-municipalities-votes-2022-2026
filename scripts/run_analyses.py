"""Run shared analysis engines (attendance, rebelity, govity, wpca) against validated city tables.

Never forks analysis formulas; invokes shared scripts in legislature-data-analyses and
validates all outputs against shared schemas in legislature-data-standard.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.standardize import ROOT, DEFAULT_SCHEMAS, transform, validate, validate_schema

ANALYSES = ("attendance", "rebelity", "govity", "wpca")


def run_attendance(city, shared, schemas, tables, city_root, config):
    defn_file = city_root / "analyses/attendance/attendance_definition.json"
    defn_file.parent.mkdir(parents=True, exist_ok=True)
    defn = {
        "since": min(e["start_date"] for e in tables["vote_events"]),
        "until": max(e["start_date"] for e in tables["vote_events"]),
        "present_options": config.get("attendance_present_options", ["yes", "no", "abstain", "not_voting"]),
        "absent_options": config.get("attendance_absent_options", ["absent"]),
    }
    defn_file.write_text(json.dumps(defn, indent=2) + "\n")

    output = city_root / "work/attendance.json"
    cmd = [
        sys.executable,
        str(shared / "attendance/attendance.py"),
        "--definition", str(defn_file),
        "--votes", str(city_root / "data/votes.csv"),
        "--vote_events", str(city_root / "data/vote_events.json"),
        "--persons", str(city_root / "work/analysis_inputs/all_members.json"),
        "--output", str(output),
    ]
    subprocess.run(cmd, check=True)
    records = json.loads(output.read_text())
    validate_schema(records, schemas, "dt.analyses/attendance/latest/schemas/attendance.dt.analyses.json")
    target = city_root / "analyses/attendance/outputs/attendance.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{city}: attendance output validated ({len(records)} members)")


def run_rebelity(city, shared, schemas, tables, city_root, config):
    defn_file = city_root / "analyses/rebelity/rebelity_definition.json"
    defn_file.parent.mkdir(parents=True, exist_ok=True)
    defn = {
        "since": min(e["start_date"] for e in tables["vote_events"]),
        "until": None,
        "present_options": ["yes", "no", "abstain"],
        "absent_options": ["absent", "not_voting"],
        "yes_options": ["yes"],
        "no_options": ["no"],
        "extras": {
            "source_status": "verified",
            "note": "Rebelity measures voting against own council club majority."
        }
    }
    defn_file.write_text(json.dumps(defn, indent=2) + "\n")

    output = city_root / "work/rebelity.json"
    cmd = [
        sys.executable,
        str(shared / "rebelity/rebelity.py"),
        "--definition", str(defn_file),
        "--votes", str(city_root / "data/votes.csv"),
        "--vote_events", str(city_root / "data/vote_events.json"),
        "--persons", str(city_root / "work/analysis_inputs/all_members.json"),
        "--output", str(output),
    ]
    subprocess.run(cmd, check=True)
    records = json.loads(output.read_text())
    validate_schema(records, schemas, "dt.analyses/rebelity/latest/schemas/rebelity.dt.analyses.json")
    target = city_root / "analyses/rebelity/outputs/rebelity.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{city}: rebelity output validated ({len(records)} members)")


def run_govity(city, shared, schemas, tables, city_root, config):
    defn_file = city_root / "analyses/govity/govity_definition.json"
    defn_file.parent.mkdir(parents=True, exist_ok=True)

    if city == "bratislava":
        gov_groups = ["bratislava:org:group:team-bratislava-ps-sas"]
        extras = {
            "coalition_status": "verified",
            "coalition_note": "Governing coalition formed by Klub Team Bratislava, PS, SaS supporting Mayor Matúš Vallo."
        }
    else:
        gov_groups = ["kosice:org:group:spolupraca-pre-kosice"]
        extras = {
            "coalition_status": "verified",
            "coalition_note": "Košice has no formal majority coalition agreement; Mayor Jaroslav Polaček and leadership are anchored in Spolupráca pre Košice."
        }

    defn = {
        "since": min(e["start_date"] for e in tables["vote_events"]),
        "until": None,
        "present_options": ["yes", "no", "abstain"],
        "absent_options": ["absent", "not_voting"],
        "yes_options": ["yes"],
        "no_options": ["no"],
        "government_groups": gov_groups,
        "government_members": [],
        "extras": extras,
    }
    defn_file.write_text(json.dumps(defn, indent=2) + "\n")

    output = city_root / "work/govity.json"
    cmd = [
        sys.executable,
        str(shared / "govity/govity.py"),
        "--definition", str(defn_file),
        "--votes", str(city_root / "data/votes.csv"),
        "--vote_events", str(city_root / "data/vote_events.json"),
        "--persons", str(city_root / "work/analysis_inputs/all_members.json"),
        "--output", str(output),
    ]
    subprocess.run(cmd, check=True)
    records = json.loads(output.read_text())
    validate_schema(records, schemas, "dt.analyses/govity/latest/schemas/govity.dt.analyses.json")
    target = city_root / "analyses/govity/outputs/govity.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{city}: govity output validated ({len(records)} members)")


def run_wpca(city, shared, schemas, tables, city_root, config):
    defn_file = city_root / "analyses/wpca/wpca_definition.json"
    defn_file.parent.mkdir(parents=True, exist_ok=True)

    rot_voter = "bratislava:person:212609" if city == "bratislava" else "kosice:person:24"
    defn = {
        "since": min(e["start_date"] for e in tables["vote_events"]),
        "until": None,
        "lo_limit": 0.1,
        "yes_options": ["yes"],
        "no_options": ["no", "abstain"],
        "absent_options": ["absent", "not_voting"],
        "rotate": {
            "voter_id": rot_voter,
            "dims": [1, 1, 1],
        },
        "time_interval": "half-year",
        "n_dims": 3,
        "extras": {
            "rotation_anchor": rot_voter,
        }
    }
    defn_file.write_text(json.dumps(defn, indent=2) + "\n")

    output = city_root / "work/wpca.json"
    output_time = city_root / "work/wpca_time.json"
    cmd = [
        sys.executable,
        str(shared / "wpca/wpca.py"),
        "--definition", str(defn_file),
        "--votes", str(city_root / "data/votes.csv"),
        "--vote-events", str(city_root / "data/vote_events.json"),
        "--persons", str(city_root / "work/analysis_inputs/all_members.json"),
        "--output", str(output),
        "--output-time", str(output_time),
    ]
    subprocess.run(cmd, check=True)
    records = json.loads(output.read_text())
    validate_schema(records, schemas, "dt.analyses/wpca/latest/schemas/wpca.dt.analyses.json")
    target = city_root / "analyses/wpca/outputs/wpca.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

    time_records = json.loads(output_time.read_text())
    validate_schema(time_records, schemas, "dt.analyses/wpca-time/latest/schemas/wpca-time.dt.analyses.json")
    target_time = city_root / "analyses/wpca/outputs/wpca_time.json"
    target_time.write_text(json.dumps(time_records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{city}: wpca output validated ({len(records)} members, {len(time_records)} time windows)")


def run(city, shared, schemas, target_analyses=None):
    city_root = ROOT / city
    tables = transform(city, json.loads((city_root / "source/reviewed.json").read_text()))
    validate(tables, schemas)
    subprocess.run([sys.executable, "-m", "scripts.standardize", city,
                    "--schemas", str(schemas)], cwd=ROOT, check=True)
    config = json.loads((city_root / "config/sources.json").read_text())

    selected = target_analyses or ANALYSES
    if "attendance" in selected:
        run_attendance(city, shared, schemas, tables, city_root, config)
    if "rebelity" in selected:
        run_rebelity(city, shared, schemas, tables, city_root, config)
    if "govity" in selected:
        run_govity(city, shared, schemas, tables, city_root, config)
    if "wpca" in selected:
        run_wpca(city, shared, schemas, tables, city_root, config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=["bratislava", "kosice"])
    parser.add_argument("--analysis", choices=list(ANALYSES), help="Run a specific analysis only")
    parser.add_argument("--shared", type=Path,
                        default=Path("/home/michal/project/legislature-data/legislature-data-analyses"))
    parser.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    args = parser.parse_args()
    run(args.city, args.shared, args.schemas, [args.analysis] if args.analysis else None)
