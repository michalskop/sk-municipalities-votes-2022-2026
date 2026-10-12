"""Write a reproducible count/provenance report for the pinned real source samples."""
import argparse
import json
from pathlib import Path

from scripts.extract_bratislava import extract as extract_ba
from scripts.extract_kosice import extract as extract_ke
from scripts.standardize import ROOT


def audit():
    records = []
    for city, extract in (("bratislava", extract_ba), ("kosice", extract_ke)):
        for path in sorted((ROOT / city / "source/extracts").glob("*.json")):
            result = extract(path)
            records.append({"city": city, "input": str(path.relative_to(ROOT)),
                            "input_sha256": result["input_sha256"], "status": result["review_status"],
                            "events": [{"id": e["id"], "date": e["date"],
                                        "votes": len(e["rows"]), "counts": e["counts"],
                                        "source_present": e["present_count"],
                                        "sources": e["sources"]} for e in result["events"]]})
    return {"scope": "pinned source samples; not full-term coverage or production data",
            "events": sum(len(r["events"]) for r in records),
            "individual_votes": sum(e["votes"] for r in records for e in r["events"]),
            "samples": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/source-sample-audit.json")
    args = parser.parse_args()
    report = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Reconciled {report['events']} events and {report['individual_votes']} individual votes")
