"""Automated visual inspection, run on every pull request and release.

Serves site/ over HTTP and opens every section at desktop (1366px) and phone
(400px) widths, in light and dark themes, with the drawer open and closed.
It fails when the page throws a script error, anything scrolls sideways, the
global navigation overflows, the in-page self-checks do not all pass (or a
negative test does not fail), or the store filters stop working.
Full-page screenshots go to qa-shots/ for a person to glance at.

Run:  pip install playwright==1.48.0 && python -m playwright install chromium
      python tools/visual_qa.py
"""
from __future__ import annotations

import functools
import http.server
import re
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "qa-shots"
VIEWS = ["overview", "store", "adopt", "developers", "directories", "ecosystem", "knowledge", "documents", "about"]
SIZES = [(1366, 900, "desktop"), (400, 860, "phone")]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main() -> int:
    SHOTS.mkdir(exist_ok=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("light", "dark"):
            for w, h, tag in SIZES:
                page = browser.new_page(viewport={"width": w, "height": h}, color_scheme=scheme)
                page.on("pageerror", lambda e, t=f"{scheme} {tag}": problems.append(f"{t}: script error: {e}"))
                page.goto(url)
                page.wait_for_timeout(800)
                summary = page.inner_text("#checksSummary")
                m = re.match(r"(\d+) of (\d+) checks pass\. (\d+) of (\d+) negative", summary)
                if not m or m.group(1) != m.group(2) or m.group(3) != m.group(4):
                    problems.append(f"{scheme} {tag}: self-checks: {summary}")
                if page.evaluate("document.querySelector('#gnav').scrollWidth > document.querySelector('#gnav').clientWidth + 1"):
                    problems.append(f"{scheme} {tag}: global navigation overflows")
                page.goto(url + "#store")  # D5: a deep link must not hide the heading under the masthead
                page.wait_for_timeout(500)
                if page.evaluate("document.querySelector('#st-h').getBoundingClientRect().top < document.querySelector('#mast').getBoundingClientRect().bottom"):
                    problems.append(f"{scheme} {tag}: heading hidden under the masthead after a deep link")
                page.click("#drawerToggle") if page.evaluate("!document.querySelector('#drawer').classList.contains('closed')") else None
                if not page.locator("#drawerToggle .tl").is_visible():  # D6: the closed toggle must keep a visible label
                    problems.append(f"{scheme} {tag}: drawer toggle has no visible label when closed")
                page.click("#drawerToggle")
                page.goto(url)
                page.wait_for_timeout(500)
                page.evaluate("location.hash='#store'")
                page.select_option("#fCat", "Payments")
                if page.locator("#storeGrid .lcard").count() != 1:
                    problems.append(f"{scheme} {tag}: category filter did not narrow the store to one listing")
                page.select_option("#fCat", "")
                for drawer in ("as loaded", "toggled"):
                    if drawer == "toggled":
                        page.click("#drawerToggle")
                        page.wait_for_timeout(250)
                    for v in VIEWS:
                        page.evaluate(f"location.hash='#{v}'")
                        page.wait_for_timeout(150)
                        if page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"):
                            problems.append(f"{scheme} {tag} {v} (drawer {drawer}): page scrolls sideways")
                        if drawer == "as loaded":
                            page.screenshot(path=str(SHOTS / f"{scheme}-{tag}-{v}.png"), full_page=True)
                page.close()
        browser.close()
    srv.shutdown()
    if problems:
        print("Visual inspection found problems:\n" + "\n".join(f"- {x}" for x in problems))
        return 1
    print(f"Visual inspection passed: {len(VIEWS)} sections x 2 widths x 2 themes x drawer open and closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
