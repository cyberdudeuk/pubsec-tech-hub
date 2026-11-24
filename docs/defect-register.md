# Defect register

_Generated from data/hub.json by tools/build.py._ Every defect has a root cause and at least one check that stops it coming back, added in the same commit as the fix.

| ID | Found | Defect | Root cause | Prevention | Checks |
|---|---|---|---|---|---|
| D1 | 2026-11-24 | Prototype carried invented figures (342 apps, 58M+ users, star ratings) | The prototype was a design mock with no data sources | Every listing figure must cite a known source; ratings fields are rejected | citations_known, no_ratings |
| D2 | 2026-11-24 | Prototype pages showed email addresses | Template housekeeping pages | Email pattern check on the page and on every data value, including harvested publiccode.yml contacts | no_emails, harvest_strips_contacts |
| D3 | 2026-11-24 | Prototype footer said the portal was operated by CDDO and used Crown branding | Copied government template | Check for retired or misleading names and Crown marks | retired_names, no_crown_marks |
| D4 | 2026-11-24 | Prototype listed a political party as a think tank | Unchecked list | Ecosystem lists hold only names and official https links, with no labels that classify organisations | ecosystem_links_https |
| D5 | 2026-11-24 | On a phone, opening a deep link such as #store hid the page heading under the sticky masthead | The browser's own anchor jump ran after the page reset its scroll position | Reset the scroll after the anchor jump; the visual inspection opens a deep link and checks the heading is visible | heading_visible |
| D6 | 2026-11-24 | With the drawer closed, its toggle showed only a switch with no visible label | The label was hidden with the drawer contents | Keep the label visible in the closed rail; the visual inspection checks it | toggle_label_visible |
| D7 | 2026-11-24 | Knowledge graph labels overlapped | Repulsion too weak for the number of nodes | Stronger spacing; the graph is also given as a text list for anyone who cannot use it | visual_qa |
| D8 | 2026-11-24 | The first sync failed: CI said the built site was out of date although it had just been built | The QR code library writes '/>' or ' />' depending on whether lxml is installed, so the build differed between machines | Normalise the QR code markup; a unit test checks it, and the build check now reports where the page differs | site_fresh, qr_normalised |
| D9 | 2026-11-24 | On phones the page scrolled sideways in CI, though not on the build machine | The masthead could not shrink with the wider fonts on CI's Linux runner, and the colophon barcode kept millimetre units inside its viewBox, so its bars spilled 3.8 times wider than the box | The masthead text now shrinks and the subtitle hides on small screens; the barcode uses plain units and clips; the visual inspection now uses a wide fallback font, adds a 360px width and names the element that sticks out | visual_qa |
| D10 | 2026-11-24 | On phones the closed drawer rail covered the left edge of the footer text | The rail is fixed to the left of the screen; the main column was padded for it but the footer was not | Pad the footer on small screens too; the visual inspection checks the closed rail does not overlap the footer | visual_qa |
