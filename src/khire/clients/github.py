from __future__ import annotations

import httpx

from khire.config import settings

GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}{path}",
                headers=self.headers,
                params=params or {},
            )
            if resp.status_code == 404:
                raise ValueError(f"GitHub resource not found: {path}")
            resp.raise_for_status()
            return resp.json()

    async def get_user(self, username: str) -> dict:
        return await self._get(f"/users/{username}")

    async def get_repos(
        self, username: str, per_page: int = 100, sort: str = "updated"
    ) -> list[dict]:
        return await self._get(
            f"/users/{username}/repos",
            params={"per_page": per_page, "sort": sort, "type": "all"},
        )

    async def get_events(self, username: str, per_page: int = 100) -> list[dict]:
        return await self._get(
            f"/users/{username}/events",
            params={"per_page": per_page},
        )
