"""Weekly harvest of publiccode.yml files.

Reads the repository list in data/harvest-sources.json, fetches each
repository's publiccode.yml (or .yaml) from raw.githubusercontent.com, keeps
only the fields the hub shows, removes every contact detail and email
address, and writes data/harvested.json.

Run:  python tools/harvest.py
Needs: pip install pyyaml==6.0.2
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "harvest-sources.json"
OUT = ROOT / "data" / "harvested.json"
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}\.[\w.]{2,}")
STATUS = {"concept", "development", "beta", "stable", "obsolete"}
REPO = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+)$")
KIND = {"standalone/mobile": "App", "standalone/web": "Product", "standalone/desktop": "Product", "standalone/backend": "Platform",
        "standalone/other": "Product", "addon": "Component library", "library": "Component library", "configurationFiles": "Tool"}


def _text(v) -> str:
    return EMAIL.sub("[removed]", str(v or "")).strip()


def _description(doc: dict) -> str:
    d = doc.get("description") or {}
    for lang in ("en-GB", "en", "eng"):
        if isinstance(d.get(lang), dict):
            return _text(d[lang].get("shortDescription") or d[lang].get("longDescription", "")[:200])
    return ""


def map_publiccode(doc: dict, repo: str) -> dict:
    """Map a parsed publiccode.yml to a hub listing. Contacts are never copied."""
    if not isinstance(doc, dict) or not doc.get("name"):
        raise ValueError("not a publiccode.yml document: missing name")
    legal = doc.get("legal") or {}
    status = str(doc.get("developmentStatus", "")).strip()
    cats = doc.get("categories") or []
    m = REPO.match(repo)
    owner = legal.get("mainCopyrightOwner") or legal.get("repoOwner") or (m.group(1) if m else "")
    landing = str(doc.get("landingURL") or "")
    return {
        "id": re.sub(r"[^a-z0-9]+", "-", str(doc["name"]).lower()).strip("-"),
        "name": _text(doc["name"]),
        "kind": KIND.get(str(doc.get("softwareType", "")), "Product"),
        "cat": _text(cats[0]).replace("-", " ").capitalize() if cats else "Other",
        "owner": _text(owner),
        "body": "Not stated",
        "nation": "UK",
        "summary": _description(doc),
        "maturity": status if status in STATUS else "Not declared",
        "licence": _text(legal.get("license") or "Not stated"),
        "code": [repo],
        "live": landing if landing.startswith("https://") else "",
        "figures": [],
        "users": [],
        "pc": True,
        "s": [],
        "tags": [_text(t) for t in (doc.get("platforms") or [])][:5],
    }


def fetch(repo: str, branch: str) -> dict | None:
    m = REPO.match(repo)
    if not m:
        raise ValueError(f"not a GitHub repository address: {repo}")
    for name in ("publiccode.yml", "publiccode.yaml"):
        url = f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{branch}/{name}"
        try:
            with urllib.request.urlopen(url, timeout=20) as r:  # fixed host built from an allowlisted pattern
                return yaml.safe_load(r.read(200_000).decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    return None


def main() -> int:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    listings, errors = [], []
    for s in sources:
        try:
            doc = fetch(s["repo"], s.get("branch", "main"))
            if doc is not None:
                listings.append(map_publiccode(doc, s["repo"]))
        except Exception as e:  # one bad repository must not stop the harvest
            errors.append(f"{s['repo']}: {e}")
    out = {"date": dt.date.today().isoformat(), "checked": len(sources), "found": len(listings), "errors": errors, "listings": listings}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"harvest: {len(listings)} of {len(sources)} repositories have publiccode.yml; {len(errors)} errors")
    for e in errors:
        print("  -", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
