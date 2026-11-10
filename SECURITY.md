# Security policy

## Supported versions

Security fixes are currently provided for the latest released version and the `main` branch.

## Reporting a vulnerability

Please do not report suspected vulnerabilities in a public issue. Use GitHub's private vulnerability reporting for this repository, if enabled, or contact the maintainers through the contact details on the repository profile.

Please include the affected version, impact, reproduction steps, and any suggested mitigation. Do not include real access tokens or private repository data.

## Security design

The CLI uses read-only GitHub API requests, executes no repository code, and has no third-party runtime dependencies. Authentication tokens are read from environment variables and must never be included in generated reports.
