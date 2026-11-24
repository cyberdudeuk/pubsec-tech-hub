"""Build site/index.html from src/ and data/.

The page is one self-contained file: the template, the sections, the footer,
the script and all data are joined here, and the QR code and barcode for the
colophon are drawn as inline SVG. Nothing loads from another site.

Run:   python tools/build.py           (writes site/index.html and site/data/)
       python tools/build.py --check   (fails if site/ is out of date)
Needs: pip install qrcode==7.4.2 python-barcode==0.15.1
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sys
from pathlib import Path

import barcode
import qrcode
import qrcode.image.svg
from barcode.writer import SVGWriter

ROOT = Path(__file__).resolve().parents[1]
SRC, DATA, SITE = ROOT / "src", ROOT / "data", ROOT / "site"
DATA_FILES = ("hub.json", "harvested.json", "reconciliation.json")


def load() -> dict:
    hub = json.loads((DATA / "hub.json").read_text(encoding="utf-8"))
    harvested = json.loads((DATA / "harvested.json").read_text(encoding="utf-8"))
    hub["reconciliation"] = json.loads((DATA / "reconciliation.json").read_text(encoding="utf-8"))
    hub["harvest"] = {k: harvested.get(k) for k in ("date", "checked", "found")}
    hub["listings"] = merge(hub["listings"], harvested.get("listings", []))
    return hub


def merge(curated: list[dict], harvested: list[dict]) -> list[dict]:
    """A harvested listing replaces the curated one for the same repository; curated facts are kept."""
    by_repo = {c["code"][0].lower(): i for i, c in enumerate(curated) if c.get("code")}
    out = [dict(c) for c in curated]
    for h in harvested:
        key = h["code"][0].lower()
        if key in by_repo:
            old = out[by_repo[key]]
            new = {**old, **{k: v for k, v in h.items() if v not in (None, "", [])}}
            new["figures"], new["users"], new["s"] = old["figures"], old.get("users", []), old["s"]
            new["id"], new["body"] = old["id"], old["body"]
            out[by_repo[key]] = new
        else:
            out.append(h)
    return out


def qr_svg(text: str) -> str:
    img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    svg = img.to_string(encoding="unicode")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"\s*/>", "/>", svg)  # D8: qrcode writes " />" with lxml and "/>" without; normalise so builds match everywhere
    return svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)


def barcode_svg(text: str) -> str:
    buf = io.BytesIO()
    barcode.get("code128", text, writer=SVGWriter()).write(buf, options={"module_height": 9, "font_size": 0, "text_distance": 1, "quiet_zone": 2, "write_text": False})
    svg = buf.getvalue().decode("utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>|<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r'\swidth="[^"]*mm"\s+height="[^"]*mm"', "", svg, count=1)
    return svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" viewBox="0 0 %s" ' % _vb(svg), 1)


def _vb(svg: str) -> str:
    rects = re.findall(r'<rect x="([\d.]+)mm" y="([\d.]+)mm" width="([\d.]+)mm" height="([\d.]+)mm"', svg)
    w = max(float(x) + float(wd) for x, _, wd, _ in rects)
    h = max(float(y) + float(ht) for _, y, _, ht in rects)
    return f"{w:.3f}mm {h:.3f}mm".replace("mm", "")


def render(hub: dict) -> str:
    meta = hub["meta"]
    edition = f"PSTH-{meta['version']}-{meta['evidence_date'].replace('-', '')}"
    page = (SRC / "template.html").read_text(encoding="utf-8")
    footer = (SRC / "footer.html").read_text(encoding="utf-8")
    footer = footer.replace("__QR__", qr_svg(meta["url"])).replace("__BARCODE__", barcode_svg(edition))
    footer = footer.replace("__EDITION__", edition).replace("__REPO__", meta["repo"])
    data = json.dumps(hub, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = page.replace("<!--__VIEWS__-->", (SRC / "views.html").read_text(encoding="utf-8"))
    page = page.replace("<!--__FOOTER__-->", footer)
    page = page.replace("/*__DATA__*/", data)
    page = page.replace("/*__APP__*/", (SRC / "app.js").read_text(encoding="utf-8"))
    return page


def docs(hub: dict) -> dict[Path, str]:
    """Markdown copies of the registers, so they read well on GitHub too."""
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
    r = hub["reconciliation"]
    rec = "# Reconciliation register: Figma Make prototype\n\n_Generated from data/reconciliation.json by tools/build.py; edit the JSON, not this file._\n\n" + r["about"] + "\n\n"
    rec += "| " + " | ".join(r["columns"]) + " |\n|" + "---|" * len(r["columns"]) + "\n"
    rec += "".join("| " + " | ".join(cell(c) for c in row) + " |\n" for row in r["rows"])
    dfx = "# Defect register\n\n_Generated from data/hub.json by tools/build.py._ Every defect has a root cause and at least one check that stops it coming back, added in the same commit as the fix.\n\n"
    dfx += "| ID | Found | Defect | Root cause | Prevention | Checks |\n|---|---|---|---|---|---|\n"
    dfx += "".join(f"| {d[0]} | {d[1]} | {cell(d[2])} | {cell(d[3])} | {cell(d[4])} | {', '.join(d[5])} |\n" for d in hub["defects"])
    return {ROOT / "docs" / "reconciliation-register.md": rec, ROOT / "docs" / "defect-register.md": dfx}


def main() -> int:
    hub = load()
    page = render(hub)
    written = docs(hub)
    out = SITE / "index.html"
    if "--check" in sys.argv:
        stale = [f for f in DATA_FILES if not (SITE / "data" / f).exists() or (SITE / "data" / f).read_bytes() != (DATA / f).read_bytes()]
        stale += [str(p.relative_to(ROOT)) for p, t in written.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        if not out.exists() or out.read_text(encoding="utf-8") != page or stale:
            print("site/ is out of date: run python tools/build.py and commit the result")
            if out.exists() and out.read_text(encoding="utf-8") != page:
                old = out.read_text(encoding="utf-8")
                i = next((k for k in range(min(len(old), len(page))) if old[k] != page[k]), min(len(old), len(page)))
                print(f"  site/index.html first differs at character {i}: {old[max(0, i - 60):i + 60]!r}")
            for f in stale:
                print(f"  stale: {f}")
            return 1
        print("site/ is up to date")
        return 0
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    for p, t in written.items():
        p.write_text(t, encoding="utf-8")
    for f in DATA_FILES:
        shutil.copyfile(DATA / f, SITE / "data" / f)
    print(f"wrote {out.relative_to(ROOT)} ({len(page.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
