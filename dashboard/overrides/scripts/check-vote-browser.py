"""Browser regression for cached vote pages (requires Python Playwright and Chromium).

Pass representative default-language and prefixed-language URLs. Run against
a clean production build and then the live deployment, not just next dev.
"""
import argparse
import json
import shutil
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="Published vote-detail URLs")
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    args = parser.parse_args()
    if len(args.urls) < 2:
        parser.error("Supply default-language and prefixed-language vote URLs")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True,
                                             args=["--no-sandbox"])
        page = browser.new_page()
        requests, errors = [], []
        page.on("request", lambda request: requests.append(request.url))
        page.on("pageerror", lambda error: errors.append(str(error)))
        for url in args.urls:
            parts = urlsplit(url)
            query = dict(parse_qsl(parts.query))
            query["layout"] = "party-first"
            deep_link = urlunsplit(parts._replace(query=urlencode(query)))
            response = page.goto(deep_link, wait_until="networkidle")
            assert response.status == 200, (url, response.status)
            page.locator('a[href="?layout=party-first"][aria-current="true"]').wait_for()
            requests.clear()
            for layout in ("tabule", "polarity-first", "wp"):
                page.locator(f'a[href="?layout={layout}"]').click()
                page.locator(f'a[href="?layout={layout}"][aria-current="true"]').wait_for()
                page.wait_for_function("layout => new URL(location.href).searchParams.get('layout') === layout",
                                       arg=layout)
            page.go_back(wait_until="networkidle")
            page.locator('a[href="?layout=polarity-first"][aria-current="true"]').wait_for()
            page.go_forward(wait_until="networkidle")
            page.locator('a[href="?layout=wp"][aria-current="true"]').wait_for()
            # Chromium may recheck the static favicon after a history change.
            page_requests = [request for request in requests if urlsplit(request).path != "/favicon.svg"]
            assert not page_requests, page_requests
            assert not errors, errors
            print(json.dumps({"url": url, "layout_page_requests": 0,
                              "deep_link_and_history": "passed", "hydration_errors": 0}))
        browser.close()


if __name__ == "__main__":
    main()
