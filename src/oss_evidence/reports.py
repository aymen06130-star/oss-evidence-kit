"""Evidence collection and deterministic Markdown/JSON rendering."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any

from .github import (
    GitHubClient,
    SearchResult,
    since_date,
    validate_login,
    validate_repository_part,
)


BOT_SUFFIXES = ("[bot]", "-bot")


def _is_bot(login: str) -> bool:
    lowered = login.casefold()
    return lowered.endswith(BOT_SUFFIXES) or lowered in {"dependabot", "renovate"}


def _pr_link(item: dict[str, Any]) -> str | None:
    link = item.get("html_url")
    if isinstance(link, str) and link.startswith("https://github.com/"):
        return link
    return None


def _generated_at() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _base_metadata(
    days: int,
    since: date,
    today: date | None = None,
) -> dict[str, Any]:
    return {
        "generated_at": _generated_at(),
        "window_days": days,
        "window_start": since.isoformat(),
        "window_end": (today or date.today()).isoformat(),
        "source": "GitHub REST Search API",
        "api_version": "2022-11-28",
    }


def build_community_report(
    client: GitHubClient,
    owner: str,
    repo: str,
    *,
    days: int = 365,
    today: date | None = None,
) -> dict[str, Any]:
    """Count non-owner human accounts with merged PRs; collaborator status is not inferred."""
    validate_login(owner)
    validate_repository_part(repo, "repository name")
    since = since_date(days, today)
    repository = client.get_repository(owner, repo)
    canonical_owner = (repository.get("owner") or {}).get("login", owner)
    full_name = repository.get("full_name", f"{owner}/{repo}")
    query = (
        f"repo:{full_name} is:pr is:merged "
        f"merged:>={since.isoformat()}"
    )
    search: SearchResult = client.search_merged_pull_requests(query)

    pr_counts: Counter[str] = Counter()
    pr_links: dict[str, list[str]] = defaultdict(list)
    owner_prs = 0
    bot_prs = 0
    for item in search.items:
        user = item.get("user") or {}
        login = user.get("login")
        if not isinstance(login, str) or not login:
            continue
        if login.casefold() == str(canonical_owner).casefold():
            owner_prs += 1
            continue
        if _is_bot(login):
            bot_prs += 1
            continue
        pr_counts[login] += 1
        link = _pr_link(item)
        if link:
            pr_links[login].append(link)

    contributors = [
        {
            "login": login,
            "merged_pr_count": pr_counts[login],
            "pull_requests": pr_links[login],
        }
        for login in sorted(
            pr_counts,
            key=lambda name: (-pr_counts[name], name.casefold()),
        )
    ]
    report = {
        "report_type": "community_builder_candidates",
        **_base_metadata(days, since, today),
        "repository": full_name,
        "repository_url": repository.get(
            "html_url",
            f"https://github.com/{full_name}",
        ),
        "repository_owner_excluded": canonical_owner,
        "merged_pull_requests_found": len(search.items),
        "merged_pull_requests_reported_by_search": search.total_count,
        "owner_authored_pull_requests_excluded": owner_prs,
        "bot_authored_pull_requests_excluded": bot_prs,
        "candidate_external_contributor_count": len(contributors),
        "candidate_external_contributors": contributors,
        "search_truncated_or_incomplete": search.truncated,
        "threshold_reference": 20,
        "threshold_candidate_met": (
            len(contributors) >= 20 and not search.truncated
        ),
        "verification_status": "candidate_count_only",
        "caveats": [
            (
                "GitHub Search identifies authors and merged PRs, but does "
                "not establish whether an author is an outside contributor."
            ),
            (
                "Organization members, repository collaborators, "
                "unrecognized bots, and affiliated accounts need manual review."
            ),
            (
                "The repository owner is excluded. Other maintainers are "
                "not automatically excluded because collaborator membership "
                "is not publicly knowable in every case."
            ),
            (
                "A search result over GitHub's 1,000-item ceiling or marked "
                "incomplete is not a complete count."
            ),
            (
                "This report is supporting evidence, not an eligibility "
                "decision or a guarantee of program approval."
            ),
        ],
    }
    return report


def build_contributor_report(
    client: GitHubClient,
    username: str,
    *,
    days: int = 365,
    today: date | None = None,
) -> dict[str, Any]:
    """Find merged PRs by a user outside repositories with the same personal owner login."""
    validate_login(username)
    since = since_date(days, today)
    query = (
        f"is:pr is:merged author:{username} "
        f"merged:>={since.isoformat()}"
    )
    search = client.search_merged_pull_requests(query)

    repo_counts: Counter[str] = Counter()
    repo_links: dict[str, list[str]] = defaultdict(list)
    excluded_owned = 0
    for item in search.items:
        repository_url = item.get("repository_url", "")
        try:
            owner_and_repo = repository_url.split("/repos/", 1)[1]
            repo_owner, repo_name = owner_and_repo.split("/", 1)[:2]
            full_name = f"{repo_owner}/{repo_name}"
        except (IndexError, ValueError):
            continue
        if repo_owner.casefold() == username.casefold():
            excluded_owned += 1
            continue
        repo_counts[full_name] += 1
        link = _pr_link(item)
        if link:
            repo_links[full_name].append(link)

    repositories = [
        {
            "repository": name,
            "merged_pr_count": repo_counts[name],
            "pull_requests": repo_links[name],
        }
        for name in sorted(
            repo_counts,
            key=lambda name: (-repo_counts[name], name.casefold()),
        )
    ]
    candidate_count = sum(repo_counts.values())
    return {
        "report_type": "active_contributor_candidates",
        **_base_metadata(days, since, today),
        "github_username": username,
        "merged_pull_requests_found": len(search.items),
        "merged_pull_requests_reported_by_search": search.total_count,
        "pull_requests_in_personally_owned_repositories_excluded": excluded_owned,
        "candidate_external_merged_pr_count": candidate_count,
        "candidate_external_repositories": repositories,
        "search_truncated_or_incomplete": search.truncated,
        "threshold_reference": 100,
        "threshold_candidate_met": (
            candidate_count >= 100 and not search.truncated
        ),
        "verification_status": "candidate_count_only",
        "caveats": [
            (
                "This search excludes repositories whose owner login exactly "
                "matches the supplied username."
            ),
            (
                "It cannot determine whether you own or control an "
                "organization-owned repository; review each result."
            ),
            (
                "The report does not verify maintainer permissions, "
                "sponsorship, employment, or other affiliation."
            ),
            (
                "GitHub Search is limited to 1,000 results and can return "
                "incomplete results."
            ),
            (
                "This report is supporting evidence, not an eligibility "
                "decision or a guarantee of program approval."
            ),
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Open-source contribution evidence report",
        "",
        f"- Generated: `{report['generated_at']}`",
        (
            f"- Window: `{report['window_start']}` to "
            f"`{report['window_end']}` ({report['window_days']} days)"
        ),
        (
            f"- Source: {report['source']} "
            f"(API `{report['api_version']}`)"
        ),
        "",
    ]
    if report["report_type"] == "community_builder_candidates":
        lines += [
            f"## {report['repository']}",
            "",
            (
                "- Candidate non-owner contributors: "
                f"**{report['candidate_external_contributor_count']}**"
            ),
            (
                "- Merged PRs returned: "
                f"{report['merged_pull_requests_found']} / "
                f"{report['merged_pull_requests_reported_by_search']} reported"
            ),
            (
                "- Owner-authored PRs excluded: "
                f"{report['owner_authored_pull_requests_excluded']}"
            ),
            (
                "- Bot-authored PRs excluded: "
                f"{report['bot_authored_pull_requests_excluded']}"
            ),
            (
                "- Search complete: "
                f"**{'no' if report['search_truncated_or_incomplete'] else 'yes'}**"
            ),
            "",
            "### Candidate contributors",
            "",
            "| GitHub login | Merged PRs |",
            "|---|---:|",
        ]
        for contributor in report["candidate_external_contributors"]:
            login = contributor["login"]
            count = contributor["merged_pr_count"]
            lines.append(
                f"| [`{login}`](https://github.com/{login}) | {count} |"
            )
        if not report["candidate_external_contributors"]:
            lines.append("| No candidates found | 0 |")
    else:
        lines += [
            f"## @{report['github_username']}",
            "",
            (
                "- Candidate merged PRs outside personally owned repositories: "
                f"**{report['candidate_external_merged_pr_count']}**"
            ),
            (
                "- Merged PRs returned: "
                f"{report['merged_pull_requests_found']} / "
                f"{report['merged_pull_requests_reported_by_search']} reported"
            ),
            (
                "- PRs in repositories with the same personal owner login "
                "excluded: "
                f"{report['pull_requests_in_personally_owned_repositories_excluded']}"
            ),
            (
                "- Search complete: "
                f"**{'no' if report['search_truncated_or_incomplete'] else 'yes'}**"
            ),
            "",
            "### Candidate repositories",
            "",
            "| Repository | Merged PRs |",
            "|---|---:|",
        ]
        for repository in report["candidate_external_repositories"]:
            name = repository["repository"]
            count = repository["merged_pr_count"]
            lines.append(
                f"| [`{name}`](https://github.com/{name}) | {count} |"
            )
        if not report["candidate_external_repositories"]:
            lines.append("| No candidate repositories found | 0 |")

    lines += [
        "",
        (
            "> **Important:** This is a candidate-evidence report, not a "
            "verified eligibility decision. Review affiliations and the "
            "program's current terms before submitting."
        ),
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in report["caveats"])
    lines.append("")
    return "\n".join(lines)
