from __future__ import annotations

import httpx


class ScholarClient:
    """Client for fetching academic paper data.

    Uses Semantic Scholar API (free, no auth needed for basic queries).
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}{path}",
                params=params or {},
            )
            if resp.status_code == 404:
                raise ValueError(f"Scholar resource not found: {path}")
            resp.raise_for_status()
            return resp.json()

    async def search_author(self, name: str, limit: int = 5) -> list[dict]:
        """Search for an author by name."""
        result = await self._get(
            "/author/search",
            params={"query": name, "limit": limit, "fields": "name,paperCount,citationCount,hIndex"},
        )
        return result.get("data", []) if isinstance(result, dict) else []

    async def get_author_papers(self, author_id: str, limit: int = 20) -> list[dict]:
        """Get papers by author ID."""
        result = await self._get(
            f"/author/{author_id}/papers",
            params={
                "limit": limit,
                "fields": "title,year,citationCount,venue,authors,externalIds",
            },
        )
        return result.get("data", []) if isinstance(result, dict) else []

    async def get_paper(self, paper_id: str) -> dict:
        """Get paper details including authors."""
        return await self._get(
            f"/paper/{paper_id}",
            params={"fields": "title,year,citationCount,venue,authors,abstract"},
        )
