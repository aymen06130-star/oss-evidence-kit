"""Small, read-only GitHub REST client. No third-party dependencies."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"

GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
REPOSITORY_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def validate_login(value: str) -> str:
    """Validate a GitHub user or organization login before using it in a search query."""
    if not GITHUB_LOGIN_RE.fullmatch(value):
        raise ValueError(
            "GitHub username/owner must be 1-39 letters, digits, or hyphens"
        )
    return value


def validate_repository_part(value: str, label: str) -> str:
    """Validate one component of a GitHub repository name."""
    if not REPOSITORY_PART_RE.fullmatch(value):
        raise ValueError(
            f"GitHub {label} must contain only letters, digits, dots, "
            "underscores, or hyphens"
        )
    return value


class GitHubAPIError(RuntimeError):
    """Raised when GitHub rejects a request or returns an unusable response."""


class _GitHubRedirectHandler(HTTPRedirectHandler):
    """Allow redirects only to the HTTPS GitHub API host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        allowed = (
            target.scheme == "https"
            and target.hostname == "api.github.com"
            and target.port in (None, 443)
            and target.username is None
            and target.password is None
        )
        if not allowed:
            raise HTTPError(
                req.full_url,
                code,
                "Refusing redirect outside https://api.github.com",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class SearchResult:
    items: list[dict]
    total_count: int
    truncated: bool


class GitHubClient:
    """Read-only GitHub API client using urllib from the Python standard library."""

    def __init__(
        self,
        token: str | None = None,
        *,
        timeout: float = 20.0,
        opener=None,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.timeout = timeout
        self._opener = opener or build_opener(_GitHubRedirectHandler()).open

    def _get_json(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
    ) -> dict:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{API_ROOT}{path}{query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "oss-evidence-kit/0.1.0",
        }
        request = Request(url, headers=headers, method="GET")
        if self.token:
            # urllib deliberately does not copy unredirected headers when following
            # a redirect. The custom handler above also rejects off-host redirects.
            request.add_unredirected_header(
                "Authorization",
                f"Bearer {self.token}",
            )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if (
                exc.code == 403
                and exc.headers.get("X-RateLimit-Remaining") == "0"
            ):
                reset = exc.headers.get("X-RateLimit-Reset", "unknown")
                raise GitHubAPIError(
                    f"GitHub API rate limit reached (reset epoch: {reset}). "
                    "Set GITHUB_TOKEN or GH_TOKEN and try again."
                ) from exc
            raise GitHubAPIError(
                f"GitHub API returned HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise GitHubAPIError(
                f"Could not reach GitHub: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise GitHubAPIError(
                f"GitHub request timed out after {self.timeout:g}s"
            ) from exc

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise GitHubAPIError("GitHub returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise GitHubAPIError("GitHub returned an unexpected JSON shape")
        return decoded

    def get_repository(self, owner: str, repo: str) -> dict:
        """Fetch public metadata for a repository."""
        validate_login(owner)
        validate_repository_part(repo, "repository name")
        return self._get_json(f"/repos/{owner}/{repo}")

    def search_merged_pull_requests(
        self,
        query: str,
        *,
        page_size: int = 100,
    ) -> SearchResult:
        """Search merged PRs, respecting the Search API's 1,000-result ceiling."""
        if not 1 <= page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")

        items: list[dict] = []
        total_count: int | None = None
        incomplete = False
        for page in range(1, 11):
            data = self._get_json(
                "/search/issues",
                {
                    "q": query,
                    "per_page": page_size,
                    "page": page,
                    "sort": "updated",
                    "order": "desc",
                },
            )
            page_items = data.get("items", [])
            if not isinstance(page_items, list):
                raise GitHubAPIError(
                    "GitHub search response did not contain an item list"
                )
            items.extend(
                item for item in page_items if isinstance(item, dict)
            )
            total_count = int(data.get("total_count", len(items)))
            incomplete = incomplete or bool(
                data.get("incomplete_results", False)
            )
            if (
                len(page_items) < page_size
                or len(items) >= total_count
                or len(items) >= 1000
            ):
                break

        reported_total = (
            total_count if total_count is not None else len(items)
        )
        # Exactly 1,000 results can still be clipped by GitHub's search ceiling.
        truncated = (
            incomplete
            or reported_total > len(items)
            or len(items) >= 1000
        )
        return SearchResult(
            items=items,
            total_count=reported_total,
            truncated=truncated,
        )


def since_date(days: int, today: date | None = None) -> date:
    """Return the inclusive lower date bound for a report window."""
    if days < 1:
        raise ValueError("days must be at least 1")
    return (today or date.today()) - timedelta(days=days)
