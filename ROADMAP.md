# Roadmap

This roadmap is a set of possible contributions, not a promise or a schedule. Open an issue before starting a larger change.

## Near-term

- [ ] CSV export for contribution reports.
- [ ] Better reporting for GitHub Search pagination limits and indexing delay.
- [ ] Optional GitHub GraphQL lookup for organization membership where the token and permissions allow it, without treating missing data as proof of external status.
- [ ] More fixtures for renamed users, deleted accounts, forks, and unusual repository ownership.

## Evidence sources to investigate

- [ ] Registry download reports for npm, PyPI, crates.io, and RubyGems, with each source and measurement window clearly attributed.
- [ ] Dependency counts from public ecosystem datasets, including freshness and coverage warnings.
- [ ] A manual-evidence format for foundation committer/maintainer status.
- [ ] A carefully sourced OpenSSF Criticality Score import. Do not substitute OpenSSF Scorecard security checks for the separate Criticality Score metric.

## Quality goals

- Keep the runtime dependency-free where practical.
- Keep all data collection read-only.
- Make reports reproducible, dated, and source-linked.
- Prefer `unknown` or `candidate` over a confident but unsupported classification.
