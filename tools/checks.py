"""Static checks for the Public Sector Tech Hub.

Each check returns a list of problems (empty means pass). tests/test_checks.py
runs every check against the real repository and against a known-bad sample,
so a check that cannot fail is caught. Every check records the defect or
requirement that made it exist (see CHECK_REASONS and docs/defect-register.md).

Run:  python tools/checks.py
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}\.[\w.]{2,}")  # bounded so the scan stays linear
RETIRED = re.compile(r"Office of the Chief Data Officer|\bOCDO\b|Data Management Team|operated by the Central Digital", re.I)
CROWN = re.compile(r"Crown Copyright 20\d\d|Royal Arms|crown-logo", re.I)
RATING_KEYS = {"rating", "ratings", "reviews", "stars", "score"}
MATURITY = {"Not declared", "concept", "development", "beta", "stable", "obsolete"}
DECISIONS = {"Keep", "Improve", "Link", "Drop"}
MAX_BYTES = 400_000
PINNED = re.compile(r"uses:\s+([\w.-]+/[\w./-]+)@([0-9a-f]{40})\b")
USES = re.compile(r"uses:\s+(\S+)")
IN_PAGE = {"search_finds", "ask_grounded", "drawer_toggle", "nav_folds"}
VISUAL = {"visual_qa", "filters_work", "users_declared_only", "heading_visible", "toggle_label_visible"}
TESTS = {"harvest_parses", "harvest_strips_contacts", "qr_normalised"}

CHECK_REASONS = {
    "no_emails": "D2: prototype pages showed email addresses",
    "retired_names": "D3: prototype said it was operated by CDDO",
    "no_crown_marks": "D3: prototype used Crown branding",
    "citations_known": "D1: prototype figures had no sources",
    "no_ratings": "D1: prototype showed invented star ratings",
    "ecosystem_links_https": "D4: prototype labelled a political party as a think tank",
}


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.text: list[str] = []
        self.scripts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
            if tag == "script" and a.get("src"):
                self.scripts.append(a["src"])
        if tag == "link" and a.get("href", "").startswith("http"):
            self.scripts.append(a["href"])

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _visible(html: str) -> str:
    p = _Page()
    p.feed(html)
    return " ".join(p.text)


def known_checks() -> set[str]:
    return {c.__name__.removeprefix("check_") for c in CHECKS} | IN_PAGE | VISUAL | TESTS | {"site_fresh"}


# ---- checks: each takes the repository state as a dict ----

def check_no_emails(s):
    found = EMAIL.findall(_visible(s["html"])) + [m for t in _strings(s["data"]) for m in EMAIL.findall(t)]
    return [f"email address found: {e}" for e in found]


def check_retired_names(s):
    hits = RETIRED.findall(_visible(s["html"])) + [m for t in _strings(s["data"]) for m in RETIRED.findall(t)]
    return [f"retired or misleading name: {h}" for h in hits]


def check_no_crown_marks(s):
    return [f"Crown mark: {h}" for h in CROWN.findall(s["html"])]


def check_sources_https(s):
    return [f"{k}: {v['url']}" for k, v in s["data"]["sources"].items() if not re.match(r"^(https://|#[\w-]+$)", v["url"])]


def check_citations_known(s):
    known = set(s["data"]["sources"])
    bad = []
    for x in s["data"]["listings"]:
        for f in x.get("figures", []):
            if f.get("s") not in known:
                bad.append(f"{x['id']}: figure cites unknown source {f.get('s')}")
        for sid in x.get("s", []):
            if sid not in known:
                bad.append(f"{x['id']}: unknown source {sid}")
    return bad


def check_no_ratings(s):
    return [f"{x['id']} has {k}" for x in s["data"]["listings"] + s["harvested"].get("listings", []) for k in RATING_KEYS & set(x)]


def check_maturity_vocab(s):
    return [f"{x['id']}: maturity '{x.get('maturity')}'" for x in s["data"]["listings"] + s["harvested"].get("listings", []) if x.get("maturity") not in MATURITY]


def check_listings_complete(s):
    need = ("id", "name", "kind", "cat", "owner", "body", "summary", "maturity", "licence", "code")
    bad, ids = [], set()
    for x in s["data"]["listings"]:
        bad += [f"{x.get('id', '?')}: missing {k}" for k in need if not x.get(k)]
        bad += [f"{x.get('id')}: code link not https: {u}" for u in x.get("code", []) if not u.startswith("https://")]
        if x.get("live") and not x["live"].startswith("https://"):
            bad.append(f"{x['id']}: live link not https")
        if x.get("id") in ids:
            bad.append(f"duplicate id {x['id']}")
        ids.add(x.get("id"))
    return bad


def check_requirements_traced(s):
    d = s["data"]
    needs = {n[0] for n in d["user_needs"]}
    known = known_checks()
    bad = []
    for rid, _, rneeds, _, checks, status in d["requirements"]:
        if not rneeds or any(n not in needs for n in rneeds):
            bad.append(f"{rid} does not trace to a known user need")
        if status != "Planned" and not checks:
            bad.append(f"{rid} has no verifying check")
        bad += [f"{rid}: unknown check {c}" for c in checks if c not in known]
    for d_ in d["defects"]:
        if len(d_) != 6 or not d_[5]:
            bad.append(f"{d_[0]}: defect has no preventing check")
        else:
            bad += [f"{d_[0]}: unknown check {c}" for c in d_[5] if c not in known]
    return bad


def check_register_complete(s):
    r = s["reconciliation"]
    bad = [f"row {i}: {len(row)} columns" for i, row in enumerate(r["rows"]) if len(row) != len(r["columns"])]
    bad += [f"row {i}: decision {row[5]!r}" for i, row in enumerate(r["rows"]) if len(row) > 5 and row[5] not in DECISIONS]
    if len(r["rows"]) < 40:
        bad.append(f"register has {len(r['rows'])} rows; the prototype has at least 40 routes and shared parts")
    return bad


def check_issue_forms(s):
    need = {"0-contact.yml", "1-correction.yml", "2-listing.yml", "3-claim.yml", "4-declare-use.yml", "5-accessibility.yml"}
    used = set(re.findall(r'data-form="([\w.-]+)"', s["html"]))
    bad = [f"missing issue form {f}" for f in sorted(need - set(s["forms"]))]
    bad += [f"page links to a form that does not exist: {f}" for f in sorted(used - set(s["forms"]))]
    if s["forms"].get("config.yml", "").find("blank_issues_enabled: false") < 0:
        bad.append("blank issues are not switched off")
    return bad


def check_directories_linked(s):
    names = " ".join(d["n"] for d in s["data"]["directories"])
    bad = [f"directory missing: {n}" for n in ("NHS login", "API catalogue", "Developers Italia", "publiccode.yml", "GitHub Repos Asset Catalogue", "Legacy Technology Observatory") if n not in names]
    return bad + [f"{d['n']}: not https" for d in s["data"]["directories"] if not d["u"].startswith("https://")]


def check_ecosystem_links_https(s):
    return [f"{k}: {i['n']}" for k, v in s["data"]["ecosystem"].items() for i in v if not i["u"].startswith("https://") or set(i) - {"n", "u"}]


def check_effort_stated(s):
    return [] if re.search(r"\d+ to \d+ minutes a week", _visible(s["html"])) else ["weekly effort is not stated on the page"]


def check_reduced_motion(s):
    return [] if "prefers-reduced-motion:reduce" in s["html"].replace(" ", "") else ["no reduced-motion rule"]


def check_size(s):
    n = len(s["html"].encode("utf-8"))
    return [f"page is {n} bytes, over {MAX_BYTES}"] if n > MAX_BYTES else []


def check_no_external_scripts(s):
    p = _Page()
    p.feed(s["html"])
    return [f"external resource: {u}" for u in p.scripts]


def check_no_eval(s):
    return ["page uses eval or new Function"] if re.search(r"\beval\(|new Function\(|innerHTML\s*=\s*location", s["html"]) else []


def check_json_ld(s):
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s["html"], re.S)
    if not m:
        return ["no JSON-LD"]
    try:
        json.loads(m.group(1))
    except ValueError as e:
        return [f"JSON-LD does not parse: {e}"]
    return []


def check_actions_pinned(s):
    bad = []
    for name, text in s["workflows"].items():
        for u in USES.findall(text):
            if not PINNED.search("uses: " + u):
                bad.append(f"{name}: action not pinned to a commit: {u}")
        if "permissions:" not in text:
            bad.append(f"{name}: no permissions block")
    return bad


CHECKS = [check_no_emails, check_retired_names, check_no_crown_marks, check_sources_https, check_citations_known, check_no_ratings,
          check_maturity_vocab, check_listings_complete, check_requirements_traced, check_register_complete, check_issue_forms,
          check_directories_linked, check_ecosystem_links_https, check_effort_stated, check_reduced_motion, check_size,
          check_no_external_scripts, check_no_eval, check_json_ld, check_actions_pinned]


def load_state(root: Path = ROOT) -> dict:
    wf = root / ".github" / "workflows"
    forms = root / ".github" / "ISSUE_TEMPLATE"
    return {
        "html": (root / "site" / "index.html").read_text(encoding="utf-8"),
        "data": json.loads((root / "data" / "hub.json").read_text(encoding="utf-8")),
        "harvested": json.loads((root / "data" / "harvested.json").read_text(encoding="utf-8")),
        "reconciliation": json.loads((root / "data" / "reconciliation.json").read_text(encoding="utf-8")),
        "forms": {p.name: p.read_text(encoding="utf-8") for p in forms.glob("*.yml")} if forms.exists() else {},
        "workflows": {p.name: p.read_text(encoding="utf-8") for p in wf.glob("*.yml")} if wf.exists() else {},
    }


def run(state: dict) -> dict[str, list[str]]:
    return {c.__name__: c(state) for c in CHECKS}


def main() -> int:
    results = run(load_state())
    failed = 0
    for name, problems in results.items():
        print(f"{'PASS' if not problems else 'FAIL'}  {name}")
        for p in problems:
            print(f"      - {p}")
        failed += bool(problems)
    print(f"\n{len(results) - failed} of {len(results)} checks pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
