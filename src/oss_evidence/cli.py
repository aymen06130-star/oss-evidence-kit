"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .github import GitHubAPIError, GitHubClient
from .reports import (
    build_community_report,
    build_contributor_report,
    render_markdown,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oss-evidence",
        description="Build read-only GitHub contribution evidence reports.",
        epilog="Set GITHUB_TOKEN or GH_TOKEN to increase the GitHub API rate limit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"oss-evidence {__version__}",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    community = commands.add_parser(
        "community",
        help="Count non-owner human accounts with merged PRs in one repository.",
    )
    community.add_argument(
        "repository",
        help="GitHub repository in OWNER/REPO form",
    )
    community.add_argument(
        "--since-days",
        type=int,
        default=365,
        help="Look-back window (default: 365)",
    )
    community.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    community.add_argument(
        "--output",
        type=Path,
        help="Write report to a file instead of stdout",
    )

    contributor = commands.add_parser(
        "contributor",
        help="Find merged PRs by a user outside personally owned repositories.",
    )
    contributor.add_argument("username", help="GitHub username")
    contributor.add_argument(
        "--since-days",
        type=int,
        default=365,
        help="Look-back window (default: 365)",
    )
    contributor.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    contributor.add_argument(
        "--output",
        type=Path,
        help="Write report to a file instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.since_days < 1:
        parser.error("--since-days must be at least 1")

    try:
        client = GitHubClient()
        if args.command == "community":
            if "/" not in args.repository:
                parser.error("repository must use OWNER/REPO form")
            owner, repo = args.repository.split("/", 1)
            report = build_community_report(
                client,
                owner,
                repo,
                days=args.since_days,
            )
        else:
            report = build_contributor_report(
                client,
                args.username,
                days=args.since_days,
            )
    except GitHubAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        output = render_markdown(report)

    try:
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Wrote report to {args.output}")
        else:
            sys.stdout.write(output)
    except OSError as exc:
        print(f"error: could not write report: {exc}", file=sys.stderr)
        return 2
    return 0
