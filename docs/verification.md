# How the hub is verified

Every change goes through the same steps, before and after the change and again after any fix.

1. **Build freshness**: `tools/build.py --check` fails if `site/` or the Markdown registers differ from what `src/` and `data/` produce.
2. **Static checks**: `tools/checks.py` runs 20 checks: no email addresses, no retired or misleading names, no Crown marks, https sources, every figure cites a known source, no ratings, maturity vocabulary, complete listings, requirements traced to needs and known checks, complete reconciliation register, issue forms present, directories linked, ecosystem links clean, effort stated, reduced motion, page size, no external scripts, no eval, valid JSON-LD, actions pinned to commits.
3. **Negative tests**: `tests/test_checks.py` builds a known-bad sample and asserts every check fails on it, so a check that cannot fail is caught. The harvester has its own tests, including that contact details are stripped.
4. **In-page self-checks**: 12 checks run in the reader's browser, each with a negative test; the About section shows the results.
5. **Visual inspection**: `tools/visual_qa.py` opens every section at 1366px and 400px, light and dark, drawer open and closed, and fails on script errors, sideways scrolling, navigation overflow, a hidden heading after a deep link, an unlabelled drawer toggle, broken filters or failing self-checks. Screenshots are attached to each CI run.
6. **Monthly link check**: `tools/maintenance.py`.

Every defect gets a root cause and a check in the same commit as its fix; see `docs/defect-register.md`. The check suite never shrinks.
