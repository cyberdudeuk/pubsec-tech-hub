# Workflow security review

Reviewed on 27 November 2026 against the GDS Way guidance on
[using GitHub Actions and workflows](https://gds-way.digital.cabinet-office.gov.uk/standards/source-code/using-github-actions.html#triggers),
which lists `workflow_run` among the triggers to avoid unless they have had a rigorous security review.
The review was done with Claude's help; the repository owner confirms it by merging this change.

## `pages.yml:workflow_run`

Runs when one of this repository's own workflows, "Sync from staging" or "Weekly harvest", completes, and only if it succeeded. Neither of those runs on pull requests, so no untrusted contributor can start this chain. The job checks out `main` explicitly (`ref: main`), never the triggering run's head, and downloads no artifacts from the triggering run, which is the "Pwn Request" risk the GDS Way warns about. No event field is interpolated into a `run:` step. Token: `contents: read`, `pages: write`, `id-token: write` (needed to publish to Pages). Third-party actions are pinned to commit SHAs.

**Outcome:** accepted. Re-review whenever the workflow or the workflows it listens to change; a code owner must approve any change to `.github/workflows`.
