# Public Sector Tech Hub

[![gds-dtx readiness: ready with exceptions, 10 of 10 GDS Way MUST checks met](docs/conformance/badge.svg)](docs/conformance/report.md)

What UK public bodies make, run and deploy, ready for you to adopt: an open app store of platforms, products and components, with the licence, code, live service and sourced facts for each. No star ratings or reviews, so nothing on it can be faked.

**Read it:** https://cyberdudeuk.github.io/pubsec-tech-hub/

It is one of three linked sites, each with one job:

| Site | Job |
|---|---|
| [GitHub Repos Asset Catalogue](https://cyberdudeuk.github.io/github-repos-asset-catalogue/) | Code that exists: what you could reuse |
| [Legacy Technology Observatory](https://cyberdudeuk.github.io/legacy-technology-observatory/) | What is old and risky: what you need to replace |
| **Public Sector Tech Hub** (this repository) | What public bodies make and run: what you can adopt |

## How listings work

- **Harvested listings** come from a `publiccode.yml` file in the product's own repository ([standard](https://github.com/italia/publiccode.yml)). A free GitHub Actions job reads them every Monday.
- **Curated listings** are written from the owner's public sources until the owner adds a `publiccode.yml`. On 24 November 2026 none of the twelve UK repositories listed had one, so every first listing is curated and labelled as such.
- **Maturity** is shown only as the owner declares it; otherwise "Not declared".
- **Users** are shown only when a public body declares its own use through the issue form.
- Contact details in `publiccode.yml` files are never copied.

Public bodies use issue forms to [list a product](../../issues/new?template=2-listing.yml), [claim a listing](../../issues/new?template=3-claim.yml) or [declare use](../../issues/new?template=4-declare-use.yml).

## Repository layout

```
src/                 page template, sections, footer and script
data/hub.json        listings, sources, directories, glossary, requirements, defects
data/harvested.json  latest harvest from publiccode.yml files
data/harvest-sources.json  repositories the harvest reads
data/reconciliation.json   page-by-page register for the original Figma prototype
site/                built page and data (do not edit by hand: run tools/build.py)
tools/build.py       builds site/ and the Markdown registers from src/ and data/
tools/harvest.py     weekly publiccode.yml harvest
tools/checks.py      static checks, each proved to fail on a bad sample
tools/visual_qa.py   automated visual inspection of every section
tools/maintenance.py monthly link check
tests/               unit tests, including a negative test for every check
docs/                registers, verification approach
```

## Automation

| Workflow | When | What it does |
|---|---|---|
| CI | Every pull request and push | Build freshness, static checks, unit tests, then visual inspection at desktop and phone widths, light and dark, drawer open and closed |
| Publish site | Push to `main`, or after a successful harvest | Runs the same checks and inspection, then publishes to GitHub Pages; a failed check blocks publishing |
| Weekly harvest | Mondays | Reads publiccode.yml files, rebuilds, checks, commits if anything changed; opens an issue if it fails |
| Monthly maintenance | 4th of each month | Checks every link; opens, updates or closes one issue |

Everything runs on free GitHub-hosted runners for public repositories, and every action is pinned to a commit.

## Keeping it running

About **30 to 60 minutes a week** for one person (estimate): read new issue forms, add accepted repositories to `data/harvest-sources.json` (or a curated listing to `data/hub.json`), run `python tools/build.py`, and glance at the weekly run. The monthly link check opens an issue only when something breaks. Running cost: nothing.

## Build and check locally

```
pip install qrcode==7.4.2 python-barcode==0.15.1 pyyaml==6.0.2
python tools/build.py && python tools/checks.py && python -m unittest discover -s tests
pip install playwright==1.48.0 && python -m playwright install chromium && python tools/visual_qa.py
```

## Contact

Use the [contact form](../../issues/new?template=0-contact.yml). Corrections and accessibility problems each have their own form. We never publish email addresses.

## Licence

Code is [MIT](LICENSE). Content and data are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Product names belong to their owners; quoted sources keep their own licences.

A personal, independent project. It is not an official government service and does not represent the policy of any department. A listing is not an endorsement, an assurance or a route to buy.

## How to cite

Use GitHub's **Cite this repository** button, which reads `CITATION.cff`.
