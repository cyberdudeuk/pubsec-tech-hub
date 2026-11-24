# Contributing

The easiest way to help is through the issue forms: list a product, claim a listing, declare use, or report a correction or accessibility problem.

If you change files:

1. Edit `src/` or `data/`, never `site/` (it is built).
2. Run `python tools/build.py`, `python tools/checks.py` and `python -m unittest discover -s tests`.
3. Every new figure needs a source in `data/hub.json`; every fixed defect needs a check that would have caught it, in the same pull request, and a line in the defect register.
4. Keep wording plain. Never add an email address, star ratings or reviews.
