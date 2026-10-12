"""Run the unmodified shared attendance engine against validated city tables."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.standardize import ROOT, DEFAULT_SCHEMAS, transform, validate


def run(city, shared, schemas):
    city_root = ROOT / city
    # Revalidate reviewed source and require its tables to have been standardized.
    tables = transform(city, json.loads((city_root / "source/reviewed.json").read_text()))
    validate(tables, schemas)
    subprocess.run([sys.executable, "-m", "scripts.standardize", city,
                    "--schemas", str(schemas)], cwd=ROOT, check=True)
    for name in ("persons.csv", "organizations.csv", "memberships.csv", "votes.csv",
                 "vote_events.json", "motions.json"):
        if not (city_root / "data" / name).is_file():
            raise ValueError("Run standardize before attendance")
    definition = city_root / "analyses/attendance/attendance_definition.json"
    definition.parent.mkdir(parents=True, exist_ok=True)
    config = json.loads((city_root / "config/sources.json").read_text())
    definition.write_text(json.dumps({"since": min(e["start_date"] for e in tables["vote_events"]),
        "until": max(e["start_date"] for e in tables["vote_events"]),
        "present_options": config.get("attendance_present_options", ["yes", "no", "abstain", "not_voting"]),
        "absent_options": config.get("attendance_absent_options", ["absent"])}, indent=2) + "\n")
    script = shared / "attendance/attendance.py"
    output = city_root / "work/attendance.json"
    subprocess.run([sys.executable, str(script), "--definition", str(definition),
                    "--votes", str(city_root / "data/votes.csv"),
                    "--vote_events", str(city_root / "data/vote_events.json"),
                    "--persons", str(city_root / "work/analysis_inputs/all_members.json"),
                    "--output", str(output)], check=True)
    records = json.loads(output.read_text())
    from scripts.standardize import validate_schema
    validate_schema(records, schemas, "dt.analyses/attendance/latest/schemas/attendance.dt.analyses.json")
    target = city_root / "analyses/attendance/outputs/attendance.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{city}: shared attendance output validated; political metrics remain disabled")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=["bratislava", "kosice"])
    parser.add_argument("--shared", type=Path,
                        default=Path("/home/michal/project/legislature-data/legislature-data-analyses"))
    parser.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS,
                        help="Validation schemas; the shared engine also requires its sibling standard/dist")
    args = parser.parse_args()
    run(args.city, args.shared, args.schemas)
