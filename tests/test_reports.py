from datetime import date

from oss_evidence.reports import build_community_report, build_contributor_report, render_markdown


class FakeClient:
    def __init__(self, repo=None, items=None, total_count=None, truncated=False):
        self.repo = repo or {"full_name": "acme/tool", "html_url": "https://github.com/acme/tool", "owner": {"login": "acme"}}
        self.items = items or []
        self.total_count = len(self.items) if total_count is None else total_count
        self.truncated = truncated
        self.queries = []

    def get_repository(self, owner, repo):
        assert (owner, repo) == ("acme", "tool")
        return self.repo

    def search_merged_pull_requests(self, query):
        from oss_evidence.github import SearchResult

        self.queries.append(query)
        return SearchResult(self.items, self.total_count, self.truncated)


def pr(login, number, repo="acme/tool"):
    return {
        "user": {"login": login},
        "html_url": f"https://github.com/{repo}/pull/{number}",
        "repository_url": f"https://api.github.com/repos/{repo}",
    }


def test_community_report_counts_unique_non_owner_humans_and_excludes_bots():
    client = FakeClient(items=[pr("acme", 1), pr("alice", 2), pr("alice", 3), pr("bob[bot]", 4), pr("carol", 5)])
    report = build_community_report(client, "acme", "tool", today=date(2026, 11, 10))

    assert report["candidate_external_contributor_count"] == 2
    assert [entry["login"] for entry in report["candidate_external_contributors"]] == ["alice", "carol"]
    assert report["owner_authored_pull_requests_excluded"] == 1
    assert report["bot_authored_pull_requests_excluded"] == 1
    assert "merged:>=2025-11-10" in client.queries[0]
    assert report["threshold_candidate_met"] is False


def test_community_markdown_includes_caveat():
    report = build_community_report(FakeClient(items=[pr("alice", 1)]), "acme", "tool")
    markdown = render_markdown(report)
    assert "Candidate non-owner contributors" in markdown
    assert "not a verified eligibility decision" in markdown
    assert "alice" in markdown


def test_contributor_report_excludes_personally_owned_repository():
    items = [
        pr("someone", 1, "octocat/project-a"),
        pr("someone", 2, "octocat/project-b"),
        pr("someone", 3, "org/project-c"),
    ]
    client = FakeClient(items=items)
    report = build_contributor_report(client, "octocat", today=date(2026, 11, 10))

    assert report["candidate_external_merged_pr_count"] == 1
    assert report["pull_requests_in_personally_owned_repositories_excluded"] == 2
    assert report["candidate_external_repositories"][0]["repository"] == "org/project-c"
    assert "merged:>=2025-11-10" in client.queries[0]


def test_truncated_search_never_marks_threshold_met():
    items = [pr(f"contributor-{i}", i) for i in range(22)]
    report = build_community_report(FakeClient(items=items, total_count=1200, truncated=True), "acme", "tool")
    assert report["candidate_external_contributor_count"] == 22
    assert report["threshold_candidate_met"] is False
    assert report["search_truncated_or_incomplete"] is True
