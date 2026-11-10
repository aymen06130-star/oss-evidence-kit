import json
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request

import pytest

from oss_evidence.github import (
    GitHubAPIError,
    GitHubClient,
    _GitHubRedirectHandler,
    since_date,
    validate_login,
)


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
        seen["auth"] = request.unredirected_hdrs.get("Authorization")
        seen["timeout"] = timeout
        return FakeResponse({"ok": True})

    client = GitHubClient("token-value", timeout=3, opener=opener)
    assert client._get_json("/repos/acme/tool") == {"ok": True}
    assert seen["auth"] == "Bearer token-value"
    assert seen["timeout"] == 3


def test_authorization_header_is_not_copied_to_redirect():
    request = Request("https://api.github.com/repos/acme/tool")
    request.add_unredirected_header("Authorization", "Bearer test-secret")

    redirected = _GitHubRedirectHandler().redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://api.github.com/repos/acme/renamed-tool",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None


def test_redirect_handler_rejects_other_hosts_and_downgrades():
    request = Request("https://api.github.com/repos/acme/tool")
    handler = _GitHubRedirectHandler()

    with pytest.raises(HTTPError, match="Refusing redirect"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://attacker.example/collect",
        )

    with pytest.raises(HTTPError, match="Refusing redirect"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "http://api.github.com/repos/acme/tool",
        )


def test_search_paginates_until_results_exhausted():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        page = int(parse_qs(urlparse(request.full_url).query)["page"][0])
        items = (
            [{"number": n} for n in range(100)]
            if page == 1
            else [{"number": 101}]
        )
        return FakeResponse(
            {
                "items": items,
                "total_count": 101,
                "incomplete_results": False,
            }
        )

    result = GitHubClient(opener=opener).search_merged_pull_requests(
        "is:pr is:merged"
    )
    assert len(result.items) == 101
    assert result.truncated is False
    assert len(calls) == 2


def test_search_preserves_incomplete_flag_from_any_page():
    def opener(request, timeout):
        page = int(parse_qs(urlparse(request.full_url).query)["page"][0])
        if page == 1:
            return FakeResponse(
                {
                    "items": [{"number": n} for n in range(100)],
                    "total_count": 101,
                    "incomplete_results": True,
                }
            )
        return FakeResponse(
            {
                "items": [{"number": 101}],
                "total_count": 101,
                "incomplete_results": False,
            }
        )

    result = GitHubClient(opener=opener).search_merged_pull_requests(
        "is:pr is:merged"
    )
    assert result.truncated is True


def test_rate_limit_error_is_actionable():
    def opener(request, timeout):
        raise HTTPError(
            request.full_url,
            403,
            "rate limited",
            {
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "123",
            },
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


def test_search_rejects_invalid_page_size():
    client = GitHubClient(opener=lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="page_size"):
        client.search_merged_pull_requests("is:pr", page_size=101)

def test_search_marks_full_1000_result_page_as_truncated():
    def opener(request, timeout):
        page = int(parse_qs(urlparse(request.full_url).query)["page"][0])
        return FakeResponse(
            {
                "items": [{"number": (page - 1) * 100 + i} for i in range(100)],
                "total_count": 1000,
                "incomplete_results": False,
            }
        )

    result = GitHubClient(opener=opener).search_merged_pull_requests(
        "is:pr is:merged"
    )
    assert len(result.items) == 1000
    assert result.truncated is True
