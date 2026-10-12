"""Extract Košice H.E.R. voting reports into a draft with explicit source totals.

Accepts saved browsing text JSON or PDF bytes (using pdftotext -layout).
Extraction does not assign mandates, canonical identities, or reviewed status.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from scripts.standardize import OPTIONS, ROOT, source_present_options
from scripts.pdf_text import layout_text

RAW_OPTIONS = {"ZA": "yes", "PROTI": "no", "ZDRŽAL SA": "abstain",
               "NEHLASOVAL": "not_voting", "NEPRÍTOMNÝ": "absent"}
# These labels are observed in the official 27 February 2025 report. Preserve
# point-in-time observations; do not extrapolate them into membership intervals.
GROUPS = ["Starostovia a nezávislí kandidáti", "Spolupráca pre Košice", "Košický klub", "Nezaradení",
          "KK", "SNK", "SPK", "N"]
MANUAL_GROUPS = ("Starostovia a nezávislí kandidáti", "Spolupráca pre Košice",
                 "Košický klub", "Nezaradení")
ROW = re.compile(r"^\s*(\d+)\s+(?:(\d+)\s+)?(.+?)\s+(NEPRÍTOMNÝ|NEHLASOVAL|ZDRŽAL SA|PROTI|ZA)\s*$")


def parse_manual_matrix(page, source_url, page_number):
    """Parse the one published six-column manual matrix for 28 October 2024."""
    if "XXV. zasadnutie" not in page or "28. október 2024" not in page:
        raise ValueError(f"Page {page_number}: manual matrix outside the reviewed Košice sitting")
    rows = []
    for line in page.splitlines():
        match = re.search(r"\s+([ZA](?:\s+[ZA]){5})\s*$", line)
        if not match:
            continue
        prefix = line[:match.start()].strip()
        group = next((name for name in MANUAL_GROUPS if prefix.endswith(name)), None)
        if not group:
            raise ValueError(f"Page {page_number}: manual matrix row has an unknown club: {line}")
        name = prefix[:-len(group)].strip()
        if not name:
            raise ValueError(f"Page {page_number}: manual matrix row has no member name")
        marks = match[1].split()
        if len(marks) != 6:
            raise ValueError(f"Page {page_number}: manual matrix does not have six votes")
        rows.append({"source_row": len(rows) + 1, "source_name": name,
                     "source_group": group, "manual_marks": marks})
    if len(rows) != 41 or len({r["source_name"] for r in rows}) != 41:
        raise ValueError(f"Page {page_number}: expected 41 unique rows in manual matrix, found {len(rows)}")

    titles = [
        "Otvorenie, zistenie prítomnosti poslancov a schválenie programu zasadnutia MZ, určenie overovateľov zápisnice, voľba návrhovej komisie",
        "Otvorenie, zistenie prítomnosti poslancov a schválenie programu zasadnutia MZ, určenie overovateľov zápisnice, voľba návrhovej komisie",
        "Otvorenie, zistenie prítomnosti poslancov a schválenie programu zasadnutia MZ, určenie overovateľov zápisnice, voľba návrhovej komisie",
        "Vyhlásenie „Podpora mesta Košice Medzinárodného maratónu mieru do ďalšej storočnice“",
        "Memorandum o partnerstve a spolupráci pri zriadení a prevádzkovaní Maratónskeho domu v Košiciach",
        "Zaradenie Medzinárodného maratónu mieru do zoznamu pamätihodností mesta Košice",
    ]
    events = []
    for vote_number, title in enumerate(titles, start=1):
        ballot = []
        for row in rows:
            mark = row["manual_marks"][vote_number - 1]
            # The results sheet reports vote 1 as a 37-person attendance check
            # with no yes/no/abstain choices. Its Z marks therefore record
            # registration, not affirmative votes. Preserve them as nonvoting.
            option = ("absent" if mark == "A" else
                      "not_voting" if vote_number == 1 else "yes")
            ballot.append({"source_row": row["source_row"], "source_name": row["source_name"],
                           "source_group": row["source_group"], "raw_option": mark,
                           "option": option})
        counts = Counter(v["option"] for v in ballot)
        published = {"present": 37, "total": 41, "missing": 4,
                     "yes": 0 if vote_number == 1 else 37,
                     "no": 0, "abstain": 0}
        events.append({"id": f"202410-2024-10-28-{vote_number:03d}", "date": "2024-10-28",
                       "title": title, "source_sitting": "202410",
                       "source_vote_number": vote_number, "sequence": vote_number,
                       "status": "test" if vote_number == 1 else "valid",
                       "source_note": ("Attendance check: the paired results sheet reports 37 present and zero choices; Z marks in the matrix are treated as registration."
                                       if vote_number == 1 else "Manual roll call; Z=ZA and A=absent."),
                       "sources": [{"url": source_url, "note": f"PDF page {page_number}"}],
                       "present_count": 37,
                       "counts": {option: counts[option] for option in OPTIONS},
                       "published_totals": published,
                       "rows": [{k: v for k, v in row.items() if k != "manual_marks"}
                                | ballot[index] for index, row in enumerate(rows)]})
    return events


def integer(text, label):
    match = re.search(re.escape(label) + r"\s*(\d+)", text)
    if not match:
        raise ValueError(f"Missing published integer: {label}")
    return int(match[1])


def published_totals(page):
    footer = page[page.index("POČET PRÍTOMNÝCH:"):]
    present = integer(footer, "POČET PRÍTOMNÝCH:")
    total = integer(footer, "POČET POSLANCOV:")
    missing = integer(footer, "POČET NEPRÍTOMNÝCH:")
    yes = integer(footer, "ZA HLASOVALO:")
    try:
        no = integer(footer, "PROTI HLASOVALO:")
        abstain = integer(footer, "ZDRŽALO SA:")
        not_voting = integer(footer, "NEHLASOVALO:")
    except ValueError:
        # The browsing extractor interleaves footer columns: the no and
        # nonvoting values follow the second line, abstentions the next line.
        match = re.search(r"ZA HLASOVALO:\s*\d+\s+ZDRŽALO SA:\s*"
                          r"PROTI HLASOVALO:\s*NEHLASOVALO:\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:H\.E\.R\.|$)", footer)
        if not match:
            raise ValueError("Unrecognized footer layout; cannot reconcile source totals")
        no, not_voting, abstain = map(int, match.groups())
    return {"present": present, "total": total, "missing": missing, "yes": yes,
            "no": no, "abstain": abstain, "not_voting": not_voting}


def parse_page(page, source_url, page_number):
    page = unicodedata.normalize("NFC", page)
    # Narrow source columns wrap this club's final word beneath the voter row.
    page = re.sub(r'Starostovia a nezávislí\s+(NEPRÍTOMNÝ|NEHLASOVAL|ZDRŽAL SA|PROTI|ZA)\s*\n\s*kandidáti(?=\s*\n)',
                  r'Starostovia a nezávislí kandidáti \1', page)
    header = re.search(r"VÝSLEDOK HLASOVANIA č\.\s*(\d+)\s*-\s*BOD č\.\s*(.+?)(?=\n\s*Riadok|\n\s*Zasadnutie)", page, re.S)
    sitting = re.search(r"Zasadnutie č\.\s*(\d+)\s*-\s*(.+?)\s+Dňa:\s*(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2})", page, re.S)
    if not header or not sitting:
        raise ValueError(f"Page {page_number}: unrecognized H.E.R. vote header")
    day = f"{sitting[5]}-{sitting[4]}-{sitting[3]}"
    if day < "2022-11-11" or day >= "2027-01-01":
        raise ValueError(f"Page {page_number}: wrong council term")
    rows = []
    for line in page.splitlines():
        match = ROW.fullmatch(line)
        if not match:
            if re.match(r"^\s*\d+\s+\d+\s+", line):
                raise ValueError(f"Page {page_number}: unknown or wrapped voter row: {line}")
            continue
        position, card, name, option = match.groups()
        if card is None and option != "NEPRÍTOMNÝ":
            raise ValueError(f"Page {page_number}: missing card for a non-absent voter")
        group = next((g for g in GROUPS if name.endswith(" " + g)), None)
        if group:
            name = name[:-(len(group) + 1)].strip()
        rows.append({"source_row": int(position), "source_card": int(card) if card else None,
                     "source_name": name, "source_group": group,
                     "raw_option": option, "option": RAW_OPTIONS[option]})
    totals = published_totals(page)
    if [r["source_row"] for r in rows] != list(range(1, totals["total"] + 1)):
        raise ValueError(f"Page {page_number}: incomplete or duplicated source roster")
    counts = Counter(r["option"] for r in rows)
    if any(counts[o] != totals[o] for o in ("yes", "no", "abstain", "not_voting")):
        raise ValueError(f"Page {page_number}: individual options disagree with published counts")
    cfg = json.loads((ROOT / 'kosice/config/sources.json').read_text())
    present_options = source_present_options(cfg, day)
    if totals["present"] != sum(counts[o] for o in present_options):
        raise ValueError(f"Page {page_number}: source present total disagrees with cast votes")
    if totals["missing"] != sum(counts[o] for o in OPTIONS if o not in present_options):
        raise ValueError(f"Page {page_number}: source missing total disagrees with nonparticipation")
    if totals["present"] + totals["missing"] != totals["total"]:
        raise ValueError(f"Page {page_number}: source roster totals disagree")
    note = re.search(r"\(\s*Poznámka:\s*(.*?)\s*\)", page)
    return {"id": f"{sitting[1]}-{day}-{int(header[1]):03d}", "date": day,
            "title": " ".join(header[2].split()), "source_time": sitting[6],
            "source_sitting": sitting[1], "source_vote_number": int(header[1]),
            "source_note": note[1] if note else None,
            "sources": [{"url": source_url, "note": f"PDF page {page_number}"}],
            "present_count": totals["present"], "counts": {o: counts[o] for o in OPTIONS},
            "published_totals": totals, "rows": rows}


def extract(path, source_url=None):
    raw = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        if not source_url:
            raise ValueError("--source-url required for original PDF input")
        text, repaired_fonts = layout_text(path)
        physical_pages = text.split("\f")
        pages = [p for p in physical_pages if p.strip()]
        transport = "pdftotext -layout"
        expected = None
        page_numbers = [i + 1 for i, p in enumerate(physical_pages) if p.strip()]
    else:
        data = json.loads(raw)
        source_url = data["url"]
        pages = data["pages"]
        transport = data["transport"]
        expected = data.get("expected_vote_numbers")
        page_numbers = data.get("page_numbers", list(range(1, len(pages) + 1)))
        repaired_fonts = []
    if len(page_numbers) != len(pages):
        raise ValueError("Page references do not match extracted pages")
    events, annotations, secret_ballots = [], [], []
    for page, number in zip(pages, page_numbers):
        if "HLASOVANIE POSLANCOV - RUČNE" in page:
            events.extend(parse_manual_matrix(page, source_url, number))
        elif "Tajné hlasovanie" in page:
            vote = re.search(r"VÝSLEDOK HLASOVANIA č\.\s*(\d+)", page)
            if not vote:
                raise ValueError(f"Page {number}: unrecognized secret ballot")
            totals = {key: integer(page, label) for key, label in {
                "present": "POČET PRÍTOMNÝCH:", "missing": "POČET NEPRÍTOMNÝCH:",
                "total": "POČET POSLANCOV:", "yes": "ZA HLASOVALO:",
                "no": "PROTI HLASOVALO:", "abstain": "ZDRŽALO SA:",
                "invalid": "NEPLATNÉ HLASY:"}.items()}
            if totals['present'] + totals['missing'] != totals['total'] or sum(totals[o] for o in ('yes', 'no', 'abstain', 'invalid')) != totals['present']:
                raise ValueError(f"Page {number}: secret ballot totals disagree")
            secret_ballots.append({"source_vote_number": int(vote[1]), "page": number,
                                   "published_totals": totals, "text": page.strip(),
                                   "reason": "Secret ballot has no individual voting options"})
        elif "VÝSLEDOK HLASOVANIA" not in page and re.search(r"Hlasovanie ručne|ZMÄTOČNÉ|hlasovanie.*(?:zmätočné|neplatné)", page, re.I):
            annotations.append({"page": number, "text": page.strip(), "review_status": "pending"})
        else:
            events.append(parse_page(page, source_url, number))
    numbers = [e["source_vote_number"] for e in events]
    if len({e["id"] for e in events}) != len(events):
        raise ValueError("Duplicate vote events across PDF pages")
    if expected is not None and sorted(numbers + [s['source_vote_number'] for s in secret_ballots]) != expected:
        raise ValueError("Extracted vote numbers differ from declared document range")
    return {"city": "kosice", "review_status": "draft", "input_sha256": hashlib.sha256(raw).hexdigest(),
            "transport": transport, "recovered_fonts": repaired_fonts,
            "annotations": annotations, "secret_ballots": secret_ballots, "events": events}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-url")
    args = parser.parse_args()
    result = extract(args.input, args.source_url)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"Extracted and reconciled {len(result['events'])} events; identities and mandates still need review")
