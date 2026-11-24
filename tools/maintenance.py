"""Monthly maintenance: check every link the hub publishes.

Writes a short Markdown report and exits 1 if any link fails, so the workflow
can open or update one "Maintenance needed" issue.

Run:  python tools/maintenance.py --out maintenance-report.md
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def links(d: dict) -> list[str]:
    out = [s["url"] for s in d["sources"].values()]
    for x in d["listings"]:
        out += x["code"] + ([x["live"]] if x.get("live") else [])
    out += [i["u"] for i in d["directories"]] + [i["u"] for v in d["ecosystem"].values() for i in v]
    return sorted({u for u in out if u.startswith("https://")})


def ok(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "pubsec-tech-hub link check"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status < 400, str(r.status)
    except urllib.error.HTTPError as e:
        return e.code in (401, 403, 429), str(e.code)  # bot-blocked pages still exist
    except Exception as e:  # network errors count as failures
        return False, type(e).__name__


def main() -> int:
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    d = json.loads((ROOT / "data" / "hub.json").read_text(encoding="utf-8"))
    bad = [(u, s) for u in links(d) for good, s in [ok(u)] if not good]
    report = "# Maintenance report\n\n" + ("All links work.\n" if not bad else "These links failed:\n\n" + "\n".join(f"- {u} ({s})" for u, s in bad) + "\n\nFix the address in data/hub.json, or remove the item if it has gone.\n")
    if out:
        out.write_text(report, encoding="utf-8")
    print(report)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
