"""GitHub REST API client with rate limiting and caching."""

import logging
import time
from typing import Dict, List, Optional, Any

import httpx
from cachetools import TTLCache

from hiring_engine.config import get_settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """Async GitHub API client with rate limit tracking and caching."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        settings = get_settings()
        self._token = token or settings.github_token
        self._cache = TTLCache(maxsize=500, ttl=3600)  # 1 hour TTL
        self._rate_remaining = 5000 if self._token else 60
        self._rate_reset = 0

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30.0,
        )
        logger.info("GitHub client initialized (authenticated=%s)", bool(self._token))

    async def _request(self, path: str) -> Any:
        """Make a rate-limited, cached request."""
        if path in self._cache:
            return self._cache[path]

        if self._rate_remaining <= 5:
            wait = max(0, self._rate_reset - time.time())
            if wait > 0:
                logger.warning("GitHub rate limit approaching, waiting %.0fs", wait)
                import asyncio
                await asyncio.sleep(min(wait, 60))

        response = await self._client.get(path)

        # Update rate limit info
        self._rate_remaining = int(response.headers.get("X-RateLimit-Remaining", self._rate_remaining))
        self._rate_reset = int(response.headers.get("X-RateLimit-Reset", 0))

        if response.status_code == 403 and self._rate_remaining == 0:
            logger.error("GitHub rate limit exceeded, reset at %d", self._rate_reset)
            return None

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()
        self._cache[path] = data
        return data

    async def get_user(self, username: str) -> Optional[Dict]:
        """Get user profile."""
        return await self._request(f"/users/{username}")

    async def get_repos(self, username: str, sort: str = "updated", per_page: int = 30) -> Optional[List[Dict]]:
        """Get user's public repositories."""
        return await self._request(f"/users/{username}/repos?sort={sort}&per_page={per_page}")

    async def get_repo_languages(self, owner: str, repo: str) -> Optional[Dict]:
        """Get language breakdown for a repo."""
        return await self._request(f"/repos/{owner}/{repo}/languages")

    async def get_repo_commits(self, owner: str, repo: str, per_page: int = 100) -> Optional[List[Dict]]:
        """Get recent commits for a repo."""
        return await self._request(f"/repos/{owner}/{repo}/commits?per_page={per_page}")

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[Dict]:
        """Get file content from a repo."""
        return await self._request(f"/repos/{owner}/{repo}/contents/{path}")

    @property
    def rate_remaining(self) -> int:
        return self._rate_remaining

    async def close(self):
        await self._client.aclose()


__all__ = ["GitHubClient"]
