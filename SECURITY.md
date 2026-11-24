# Security policy

The site is a static page with no server, accounts or tracking.

## Reporting a problem

Please report security problems privately using GitHub's **Report a vulnerability** button on the [Security tab](https://github.com/cyberdudeuk/pubsec-tech-hub/security). Don't open a public issue. We aim to respond within 10 working days.

## How the code is kept safe

- Every value from data is escaped before display; the page uses no `eval` or HTML from viewers.
- The page loads nothing from other sites: no scripts, fonts or trackers; the checks fail otherwise.
- The harvester fetches only from raw.githubusercontent.com, parses YAML with a safe loader and never copies contact details.
- Workflows use the least permission they need, and every third-party action is pinned to a commit.
- Dependabot proposes action updates monthly.
