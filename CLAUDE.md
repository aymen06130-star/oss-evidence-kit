# Project instructions for Claude Code

## Project purpose

OSS Evidence Kit is a read-only Python CLI that turns public GitHub Search API results into candidate-evidence reports for open-source contribution activity.

## Important product boundary

- Do not claim that an account is a verified external contributor based only on its GitHub login.
- Do not infer that a repository is not owned or controlled by an applicant just because it is under an organization owner.
- Never state that a report guarantees program eligibility or acceptance.
- Keep the GitHub API client read-only (`GET` only). Do not add code that creates issues, comments, pull requests, releases, or repository changes.
- Do not log or serialize authentication tokens.

## Development commands

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Engineering conventions

- Target Python 3.11+.
- Keep runtime dependencies at zero unless there is a documented, compelling reason to add one.
- Use type hints for public functions.
- Keep time windows explicit and report the selected dates.
- Add tests for API errors, incomplete searches, and edge cases.
- Do not use live GitHub API calls in the test suite.
