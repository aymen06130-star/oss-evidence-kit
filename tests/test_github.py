import json
from urllib.parse import parse_qs, urlparse
from io import BytesIO
from urllib.error import HTTPError

import pytest

from oss_evidence.github import GitHubAPIError, GitHubClient, since_date, validate_login


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_get_json_sends_auth_header_and_parses_response():
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        seen["timeout"] = timeout
        return FakeResponse({"ok": True})

    client = GitHubClient("token-value", timeout=3, opener=opener)
    assert client._get_json("/repos/acme/tool") == {"ok": True}
    assert seen["auth"] == "Bearer token-value"
    assert seen["timeout"] == 3


def test_search_paginates_until_results_exhausted():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        page = int(parse_qs(urlparse(request.full_url).query)["page"][0])
        items = [{"number": n} for n in range(100)] if page == 1 else [{"number": 101}]
        return FakeResponse({"items": items, "total_count": 101, "incomplete_results": False})

    result = GitHubClient(opener=opener).search_merged_pull_requests("is:pr is:merged")
    assert len(result.items) == 101
    assert result.truncated is False
    assert len(calls) == 2


def test_rate_limit_error_is_actionable():
    def opener(request, timeout):
        raise HTTPError(
            request.full_url,
            403,
            "rate limited",
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123"},
            BytesIO(b"rate limit"),
        )

    with pytest.raises(GitHubAPIError, match="Set GITHUB_TOKEN"):
        GitHubClient(opener=opener).get_repository("acme", "tool")


def test_since_date_rejects_zero_days():
    with pytest.raises(ValueError):
        since_date(0)


def test_validate_login_rejects_search_syntax():
    with pytest.raises(ValueError):
        validate_login("octocat is:merged")
