# Security policy

## Supported versions

Security fixes are currently provided for the latest released version and the `main` branch.

## Reporting a vulnerability

Please do not report suspected vulnerabilities in a public issue. Use GitHub's private vulnerability reporting for this repository, if enabled, or contact the maintainers through the contact details on the repository profile.

Please include the affected version, impact, reproduction steps, and any suggested mitigation. Do not include real access tokens or private repository data.

## Security design

- The CLI uses read-only GitHub API `GET` requests and executes no repository code.
- Runtime dependencies are limited to Python's standard library.
- Authentication tokens are read from `GITHUB_TOKEN` or `GH_TOKEN`, and are never written to reports or deliberately printed.
- Requests are sent to the fixed HTTPS GitHub REST API host. Redirects to other hosts, non-HTTPS URLs, and credential-bearing URLs are rejected.
- The Authorization header is marked as unredirected, so urllib does not copy it to a redirected request.
- CI runs linting and unit tests with read-only GitHub Actions permissions. Third-party Actions are pinned to full commit SHAs.

## Security scanning status

The CI workflow is not a substitute for dedicated vulnerability scanning. Enable GitHub CodeQL default setup and review Secret Scanning / push protection in the repository's **Settings → Security and analysis** page. A clean manual review or passing test suite is not proof that no unknown vulnerability exists.
