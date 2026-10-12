"""Inventory official meetings and preserve relevant source files; never infer votes.

Run: python -m scripts.collect_sources kosice (requires network access).
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qsl

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def meeting_links(html, base, pattern):
    soup = BeautifulSoup(html, "html.parser")
    return sorted({
        urljoin(base, a["href"]).split("#")[0].split("?")[0]
        for a in soup.select("a[href]")
        if re.fullmatch(pattern, urlparse(urljoin(base, a["href"])).path)
        and urlparse(urljoin(base, a["href"])).hostname == urlparse(base).hostname
    })


def document_links(html, base):
    """Keep all voting PDFs, minutes, attendance, and aggregate-result documents."""
    soup = BeautifulSoup(html, "html.parser")
    results = {}
    for a in soup.select("a[href]"):
        url = urljoin(base, a["href"])
        label = a.get_text(" ", strip=True)
        relevant = re.search(r"hlasovan|zápisnic|dochádz|účasť|výsledky", label, re.I)
        # Košice's minutes link is often labelled only "PDF".
        relevant = relevant or "/meeting/memorandum/" in url
        if relevant and urlparse(url).path.lower().endswith(".pdf"):
            results[url] = {"url": url, "label": label}
    return [results[url] for url in sorted(results)]


def agenda_links(html, meeting_url):
    """Bratislava publishes named voting lists on individual agenda-item pages."""
    parsed_meeting = urlparse(meeting_url)
    meeting_paths = {parsed_meeting.path.rstrip('/'),
                     parsed_meeting.path.rstrip('/').replace('-2022-2026', '')}
    soup = BeautifulSoup(html, "html.parser")
    return sorted({urljoin(meeting_url, a["href"]).split("#")[0].split("?")[0]
                   for a in soup.select("a[href]")
                   if urlparse(urljoin(meeting_url, a["href"])).hostname == parsed_meeting.hostname
                   and any(re.fullmatch(r'(?:/\d+-sk)?' + re.escape(path) + r'/bod-[^/]+/?',
                                        urlparse(urljoin(meeting_url, a['href'])).path)
                           for path in meeting_paths)})


def detail_page_links(html, meeting_url):
    """Keep program pagination and observed meeting-specific voting-tab links."""
    base = urlparse(meeting_url)
    soup = BeautifulSoup(html, "html.parser")
    return sorted({urljoin(meeting_url, a["href"]).split("#")[0] for a in soup.select("a[href]")
                   if urlparse(urljoin(meeting_url, a["href"])).hostname == base.hostname
                   and urlparse(urljoin(meeting_url, a["href"])).path == base.path
                   and re.search(r"(?:page|rokovanie_tab_\d+)=", urlparse(urljoin(meeting_url, a["href"])).query)})


def agenda_voting_links(html, agenda_url):
    """Follow the observed voting tab; its numeric item ID cannot be guessed."""
    base = urlparse(agenda_url)
    soup = BeautifulSoup(html, "html.parser")
    return sorted({urljoin(agenda_url, a["href"]).split("#")[0]
                   for a in soup.select("a[href]")
                   if urlparse(urljoin(agenda_url, a["href"])).hostname == base.hostname
                   and urlparse(urljoin(agenda_url, a["href"])).path == base.path
                   and re.search(r"(?:^|&)bod-typ-\d+=hlasovania(?:&|$)",
                                 urlparse(urljoin(agenda_url, a["href"])).query)})


def voting_page_links(html, voting_url):
    """Return observed page links; caller must establish and record tab context."""
    base = urlparse(voting_url)
    context = [(k, v) for k, v in parse_qsl(base.query) if re.fullmatch(r'rokovanie_tab_\d+', k) and v == '2']
    if len(context) != 1:
        raise ValueError('Expected one observed meeting voting-tab parameter')
    results = set()
    for target in detail_page_links(html, voting_url):
        parsed = urlparse(target)
        pagination = [(k, v) for k, v in parse_qsl(parsed.query) if k == 'page']
        if pagination:
            results.add(target)
    return sorted(results)


def collect(city, limit=None, refresh=False):
    cfg = json.loads((ROOT / city / "config/sources.json").read_text())
    work = ROOT / city / "work/sources"
    work.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "DataTimes municipal vote source inventory"
    receipts = work / "downloads.json"
    fetched = json.loads(receipts.read_text()) if receipts.exists() else []
    cached = {(row["url"], row.get('view_context')): row for row in fetched}

    def fetch(url, context=None, force=False):
        key = (url, context)
        if not refresh and not force and key in cached:
            row = cached[key]
            path = work / row["file"]
            # Resume today's work, but re-fetch on later days so corrections and
            # newly published archive entries cannot be hidden by stale caches.
            if path.is_file() and row.get('retrieved_at', '')[:10] == datetime.now(timezone.utc).date().isoformat():
                content = path.read_bytes()
                if hashlib.sha256(content).hexdigest() == row["sha256"]:
                    return "" if content.startswith(b"%PDF-") else content.decode("utf-8")
        response = session.get(url, timeout=(15, 120))
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        is_pdf = response.content.startswith(b"%PDF-")
        if urlparse(url).path.lower().endswith(".pdf") and not is_pdf:
            raise ValueError(f"Expected PDF, received another format: {url}")
        name = digest + (".pdf" if is_pdf else ".html")
        (work / name).write_bytes(response.content)
        row = {"url": url, "sha256": digest, "file": name,
               "retrieved_at": datetime.now(timezone.utc).isoformat(),
               **({'view_context': context} if context else {})}
        fetched[:] = [r for r in fetched if (r["url"], r.get('view_context')) != key]
        fetched.append(row)
        cached[key] = row
        # Preserve provenance even if a later source file fails to download.
        receipt = work / "downloads.json.tmp"
        receipt.write_text(json.dumps(fetched, ensure_ascii=False, indent=2) + "\n")
        receipt.replace(work / "downloads.json")
        time.sleep(0.25)
        return response.text if not is_pdf else ""

    # Follow same-site pagination rather than treating the first archive page as a term.
    pending, seen, meetings = [cfg["archive_url"]], set(), set()
    while pending:
        url = pending.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if len(seen) > 100:
            raise ValueError("Archive pagination exceeded 100 pages; inspect the source")
        html = fetch(url)
        meetings.update(meeting_links(html, cfg["archive_url"], cfg["meeting_pattern"]))
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]"):
            target = urljoin(url, a["href"]).split("#")[0]
            parsed = urlparse(target)
            if (parsed.hostname == urlparse(cfg["archive_url"]).hostname
                    and parsed.path == urlparse(cfg["archive_url"]).path
                    and re.search(r"(?:page|strana|offset)=", parsed.query)
                    and target not in seen and target not in pending):
                pending.append(target)
    if not meetings:
        raise ValueError("No meeting links discovered; source format may have changed")
    inventory = []
    selected = sorted(meetings)[:limit] if limit else sorted(meetings)
    for url in selected:
        html = fetch(url)
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        if city == "bratislava":
            match = re.search(r"zasadnutie-(\d{2})(\d{2})(\d{4})", url)
            date = f"{match[3]}-{match[2]}-{match[1]}"
            # Calendar 2022 also includes the previous council term.
            # Individual oath/replacement dates still require roster review.
            if date < (cfg.get("term_start") or "2022-11-01") or date >= "2027-01-01":
                continue
        else:
            match = re.search(r"Dátum konania:\s*(\d{2})\.(\d{2})\.(\d{4})", text)
            if not match:
                raise ValueError(f"Missing meeting date: {url}")
            date = f"{match[3]}-{match[2]}-{match[1]}"
        docs = document_links(html, url)
        agenda, detail_urls, voting_urls, agenda_titles = set(), set(), set(), {}
        voting_sources = []
        if city == "bratislava":
            pages = [(url, html)]
            detail_seen = {url}
            while pages:
                page_url, page_html = pages.pop(0)
                agenda.update(agenda_links(page_html, url))
                for a in BeautifulSoup(page_html, 'html.parser').select('a[href]'):
                    target = urljoin(page_url, a['href'])
                    if target in agenda and not urlparse(target).query:
                        agenda_titles[target] = a.get_text(' ', strip=True)
                docs.extend(document_links(page_html, page_url))
                for detail_url in detail_page_links(page_html, url):
                    # Finish program discovery before switching the session tab.
                    if re.search(r'rokovanie_tab_\d+=', urlparse(detail_url).query):
                        continue
                    if detail_url in detail_seen:
                        continue
                    detail_seen.add(detail_url)
                    detail_urls.add(detail_url)
                    if len(detail_seen) > 100:
                        raise ValueError(f"Meeting pagination exceeded 100 pages: {url}")
                    pages.append((detail_url, fetch(detail_url)))
            tabs = [target for target in detail_page_links(html, url)
                    if re.search(r'rokovanie_tab_\d+=2(?:&|$)', urlparse(target).query)]
            for tab in tabs:
                context = urlparse(tab).query
                # Selecting a tab redirects and discards pagination parameters.
                # Bootstrap cookies first; then fetch bare page links in that
                # context. Never reuse program HTML as voting-page HTML.
                vote_pages = [(tab, fetch(tab, context=context, force=True))]
                vote_seen = {tab}
                while vote_pages:
                    vote_url, vote_html = vote_pages.pop(0)
                    if BeautifulSoup(vote_html, 'html.parser').select('.panel.hlasovania'):
                        voting_urls.add(vote_url)
                        voting_sources.append(cached[(vote_url, context)])
                    for next_page in voting_page_links(vote_html, tab):
                        if next_page not in vote_seen:
                            vote_seen.add(next_page)
                            if len(vote_seen) > 100:
                                raise ValueError(f'Voting pagination exceeded 100 pages: {url}')
                            vote_pages.append((next_page, fetch(next_page, context=context)))
            # The meeting voting tab includes procedural votes with no agenda
            # item, as well as ordinary decisions. Prefer it when available.
            if not voting_urls:
                for agenda_url in sorted(agenda):
                    agenda_html = fetch(agenda_url)
                    for voting_url in agenda_voting_links(agenda_html, agenda_url):
                        fetch(voting_url)
                        voting_urls.add(voting_url)
                        voting_sources.append(cached[(voting_url, None)])
        docs = list({doc["url"]: doc for doc in docs}.values())
        for doc in docs:
            fetch(doc["url"])
        inventory.append({"url": url, "date": date, "documents": docs,
                          "agenda_urls": sorted(agenda), "detail_urls": sorted(detail_urls),
                          "voting_urls": sorted(voting_urls),
                          "voting_sources": voting_sources,
                          "agenda_titles": agenda_titles,
                          "roll_calls_reviewed": False})
        result = {"city": city, "limited_scan": limit is not None, "coverage_verified": False,
                  "archive_urls": sorted(seen), "discovered_meeting_urls": sorted(meetings),
                  "collection_complete": False, "meetings": inventory, "downloads": fetched}
        checkpoint = work / "inventory.json.tmp"
        checkpoint.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        checkpoint.replace(work / "inventory.json")
        print(f"{city}: collected {date} ({len(inventory)}/{len(selected)} meetings)", flush=True)
    result = {"city": city, "limited_scan": limit is not None, "coverage_verified": False,
              "archive_urls": sorted(seen), "discovered_meeting_urls": sorted(meetings),
              "collection_complete": True,
              "meetings": inventory, "downloads": fetched}
    (work / "inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"{city}: {len(inventory)} meetings inventoried; votes still require extraction and review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=["bratislava", "kosice"])
    parser.add_argument("--limit", type=int, help="Discovery smoke test only; not full-term coverage")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch even files downloaded today")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    collect(args.city, args.limit, args.refresh)
