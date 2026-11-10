# OSS Evidence Kit

**A read-only CLI for collecting reproducible evidence about open-source contributions on GitHub.**

OSS Evidence Kit currently helps investigate two contribution-based routes:

- **Community builders:** candidate unique non-owner accounts with merged pull requests in one repository during a chosen window (default: 365 days).
- **Active contributors:** candidate merged pull requests by a GitHub user in repositories whose owner login differs from that user's personal username (default: 365 days).

It turns public GitHub search results into a timestamped Markdown or JSON report, including the pull-request links used to produce the count. It does not create issues, comments, pull requests, releases, or repository changes.

> **Important:** This tool does not certify eligibility. GitHub's public API cannot reliably tell whether every non-owner contributor is genuinely external, whether someone controls an organization-owned repository, or whether an applicant is affiliated with a project. Reports are evidence candidates that a human must review against the program's current rules.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m pip install .

# Candidate contributors to a repository, over the last 365 days
oss-evidence community OWNER/REPO

# Machine-readable JSON
oss-evidence community OWNER/REPO --format json --output community.json

# A contributor's candidate merged PR activity
oss-evidence contributor GITHUB_USERNAME --format markdown --output contributor.md
```

You can also run it from a source checkout without installing the console script:

```bash
python -m oss_evidence community OWNER/REPO
```

### Increase the GitHub API rate limit

Unauthenticated GitHub API access is rate-limited. Create a fine-grained or classic personal access token with only the public repository read access you need, then set it in your shell:

```bash
export GITHUB_TOKEN="github_pat_..."
# or: export GH_TOKEN="github_pat_..."
```

The token is read from the process environment and sent only to `api.github.com` over HTTPS. It is not written to reports or local files. Never paste a token into an issue, pull request, report, or command-line argument.

## Commands

| Command | Purpose |
|---|---|
| `oss-evidence community OWNER/REPO` | Find unique non-owner human accounts with merged PRs in one repository |
| `oss-evidence contributor USERNAME` | Find merged PRs by a user outside repositories with the same personal owner login |

Common options:

| Option | Default | Description |
|---|---:|---|
| `--since-days N` | `365` | Look-back window, in days |
| `--format markdown\|json` | `markdown` | Output format |
| `--output PATH` | stdout | Save the report to a file |
| `--version` | — | Print the installed version |

The tool exits with code `0` when a report is created and `2` when the GitHub API or input fails. A threshold candidate count is not treated as a pass/fail eligibility decision.

## What it measures

### Community-builder candidate report

```bash
oss-evidence community OWNER/REPO --since-days 365 --format json
```

It searches merged pull requests in the repository, excludes the repository owner's login and recognizable bot accounts, groups the remaining PRs by GitHub login, and records the matching PR URLs. The report includes both the number of results returned and the total reported by GitHub Search. If search is incomplete or exceeds GitHub's 1,000-result search ceiling, the report marks itself as truncated and will not mark the threshold as a candidate match.

### Active-contributor candidate report

```bash
oss-evidence contributor USERNAME --since-days 365
```

It searches merged PRs authored by the user and excludes repositories whose owner login exactly matches the supplied personal username. It lists candidate repositories and PR URLs. It cannot infer whether the user owns or controls an organization account, so review the repository list before using the count.

## Safety and privacy

- Read-only: the client uses GitHub `GET` endpoints only.
- No third-party runtime dependencies; the HTTP client uses Python's standard library.
- No LLM calls, telemetry, analytics, or remote report storage.
- No code from repositories, pull requests, or issue bodies is executed.
- Reports contain public GitHub usernames and public pull-request URLs. Store and share them appropriately.
- Authentication tokens are not included in output.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [the methodology](docs/methodology.md), and [eligibility notes](docs/eligibility-notes.md).

## Project status

This is an early, deliberately narrow release. It currently reports GitHub contribution evidence for two routes only. It does **not** calculate dependent repositories, dependent packages, registry downloads, foundation committer status, or OpenSSF criticality scores. Do not infer those facts from stars, forks, or this report.

The project itself has no adoption claim. A new repository does not meet maintainer, community, or critical-infrastructure thresholds simply because it has been created. Real downstream use and independently verifiable contribution history take time.

## License

MIT. See [LICENSE](LICENSE).

## Publish this project on GitHub

After reviewing the code and replacing any project details you want to personalize:

```bash
git init -b main
git add .
git commit -m "chore: initial OSS Evidence Kit release"
gh auth login
gh repo create oss-evidence-kit --public --source . --remote origin --push
```

This creates the remote repository under the GitHub account currently authenticated with `gh`. The repository starts with no outside contributors or adoption metrics; those must be earned through genuine use and collaboration.
