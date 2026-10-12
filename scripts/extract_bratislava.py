"""Extract Bratislava's named option lists, preserving draft status and identities.

Input: saved web-rendered vote text JSON, or downloaded agenda-item HTML.
HTML mode requires an explicit date and source URL. Missing lists fail validation.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

LABELS = {"Hlasovali za": "yes", "Hlasovali proti": "no", "Zdržali sa hlasovania": "abstain",
          "Nehlasovali": "not_voting", "Neprítomní": "absent"}


def parse_vote_text(text, day, source_url, title):
    text = unicodedata.normalize("NFC", text)
    matches = list(re.finditer(r"Hlasovanie číslo\s+(\d+)", text))
    if not matches:
        raise ValueError("No named voting blocks found; voting tab may need fetching")
    if day < "2022-11-15" or day >= "2027-01-01":
        raise ValueError("Wrong council term")
    events = []
    for i, header in enumerate(matches):
        block = text[header.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        sections = list(re.finditer(r"(" + "|".join(map(re.escape, LABELS)) + r"):\s*(\d+)", block))
        if len(sections) != len(LABELS) or {s[1] for s in sections} != set(LABELS):
            raise ValueError("Each voting block must contain all five distinct option counts")
        rows, counts = [], {}
        for j, section in enumerate(sections):
            option, expected = LABELS[section[1]], int(section[2])
            body = block[section.end():sections[j + 1].start() if j + 1 < len(sections) else len(block)]
            names = [re.sub(r"^\s*\*\s*", "", line).strip() for line in body.splitlines()
                     if line.strip() and "Neboli nájdené žiadne záznamy" not in line]
            if len(names) != expected:
                raise ValueError(f"{section[1]}: published {expected}, extracted {len(names)} names")
            counts[option] = expected
            rows.extend({"source_name": name, "raw_option": section[1], "option": option}
                        for name in names)
        if len({r["source_name"] for r in rows}) != len(rows):
            raise ValueError("A person appears in more than one voting option list")
        if not rows:
            raise ValueError("Empty voting block")
        resolution = re.search(r"Uznesenie:\s*Uznesenie\s*([\w/-]+)", block)
        events.append({"id": f"{day}-{int(header[1]):03d}", "date": day, "title": title,
                       "source_vote_number": int(header[1]),
                       "source_resolution": resolution[1] if resolution else None,
                       "sources": [{"url": source_url}], "counts": counts,
                       "present_count": sum(v for o, v in counts.items() if o != "absent"),
                       "rows": rows})
    if len({e["id"] for e in events}) != len(events):
        raise ValueError("Repeated event ID; check source voting blocks")
    return events


def extract(path, source_url=None, day=None):
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        text, day, source_url, title = data["text"], data["date"], data["url"], data["title"]
        transport = data["transport"]
    else:
        if not source_url or not day:
            raise ValueError("--source-url and --date required for HTML input")
        soup = BeautifulSoup(raw, "html.parser")
        panels = soup.select(".panel.hlasovania")
        if panels:
            events = []
            for panel in panels:
                heading = panel.select_one(".panel-heading[id]")
                if heading is None:
                    raise ValueError("Voting panel has no source identifier")
                sections = panel.select(".hlasovanie-panel")
                if len(sections) != 5:
                    raise ValueError("Voting panel must contain all five option lists")
                lines = [heading.get_text("\n", strip=True)]
                identities = {}
                for section in sections:
                    label = section.select_one(".panel-heading")
                    if label is None:
                        raise ValueError("Missing option heading")
                    lines.append(label.get_text(" ", strip=True))
                    for li in section.select("ul.poslanci > li"):
                        name = li.get_text(" ", strip=True)
                        anchor = li.select_one("a[href]")
                        if anchor is None:
                            raise ValueError("Named voter has no official profile link")
                        profile = urljoin(source_url, anchor["href"])
                        identifier = re.search(r"/(\d+)-sk/", profile)
                        if identifier:
                            person_id = identifier[1]
                        elif urlparse(profile).hostname == 'zastupitelstvo.bratislava.sk' and re.fullmatch(r'/[a-z0-9-]+/', urlparse(profile).path):
                            person_id = 'slug-' + urlparse(profile).path.strip('/')
                        else:
                            raise ValueError("Unrecognized official person identifier")
                        identities[name] = {"source_person_id": person_id,
                                            "source_profile_url": profile}
                        lines.append(name)
                event = parse_vote_text("\n".join(lines), day, source_url,
                                        soup.title.get_text(strip=True) if soup.title else "Menovité hlasovanie")[0]
                event["source_record_id"] = heading["id"]
                agenda = heading.find('b', string=re.compile('Bod:'))
                link = agenda.parent.select_one('a[href]') if agenda else None
                if link:
                    event['source_agenda_url'] = urljoin(source_url, link['href']).split('?')[0].split('#')[0]
                    event['source_agenda_number'] = link.get_text(' ', strip=True)
                note = heading.find("b", string=re.compile("Poznámka"))
                event["source_note"] = note.parent.get_text(" ", strip=True) if note else None
                for row in event["rows"]:
                    row.update(identities[row["source_name"]])
                if len({r["source_person_id"] for r in event["rows"]}) != len(event["rows"]):
                    raise ValueError("Duplicate official person ID in vote")
                events.append(event)
            if len({e["id"] for e in events}) != len(events):
                raise ValueError("Repeated event ID in HTML")
            return {"city": "bratislava", "review_status": "draft",
                    "input_sha256": hashlib.sha256(raw).hexdigest(),
                    "transport": "original HTML voting panels with official person links", "events": events}
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        # HTML may separate a label and count into adjacent text nodes.
        text = re.sub(r"(Hlasovanie číslo)\s*\n\s*(\d+)", r"\1 \2", text)
        for label in LABELS:
            text = re.sub(re.escape(label) + r":\s*\n\s*(\d+)", label + r": \1", text)
        first = re.search(r"Hlasovanie číslo\s+\d+", text)
        if not first:
            raise ValueError("No named voting content in HTML")
        text = text[first.start():]
        title = soup.title.get_text(strip=True) if soup.title else "Menovité hlasovanie"
        transport = "downloaded HTML via BeautifulSoup; list boundaries require source regression checks"
    return {"city": "bratislava", "review_status": "draft", "input_sha256": hashlib.sha256(raw).hexdigest(),
            "transport": transport, "events": parse_vote_text(text, day, source_url, title)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--date")
    args = parser.parse_args()
    result = extract(args.input, args.source_url, args.date)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"Extracted and reconciled {len(result['events'])} events; identities and mandates still need review")
