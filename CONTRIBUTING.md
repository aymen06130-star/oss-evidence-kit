# Contributing

Thanks for considering a contribution to OSS Evidence Kit. The project is small and aims to keep reports deterministic, conservative, and easy to audit.

## Before opening an issue

- Search existing issues for duplicates.
- For a bug report, include the command, Python version, operating system, and a redacted error message.
- Never include GitHub tokens, private repository contents, or other credentials.

## Development setup

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Pull requests

- Keep changes focused and explain the user-facing problem.
- Add tests for behavior changes, including API edge cases where practical.
- Keep runtime dependencies at zero unless a strong reason is documented.
- Do not add write operations to the GitHub client without a separate design and explicit security review.
- Preserve caveats: candidate counts must not be presented as verified eligibility.
- Never commit real tokens, private evidence, or generated personal reports.

## Reporting security issues

Please follow [SECURITY.md](SECURITY.md) rather than opening a public issue for a suspected vulnerability.
