import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from khire.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_search_endpoint():
    mock_search_result = {
        "query": "Find ML engineers",
        "intent": {"search_queries": ["ml engineer"], "required_skills": ["python"], "min_stars": 0, "role_type": "ml_engineer", "keywords": ["ml"]},
        "candidates": [
            {
                "username": "ml_expert",
                "overall_score": 0.85,
                "user_info": {"name": "ML Expert", "bio": "ML researcher", "company": "OpenAI", "location": "SF", "followers": 5000},
                "metrics": {"repo_influence": 0.9, "pr_quality": 0.8, "collaboration": 0.7, "consistency": 0.8, "language_diversity": 0.5},
                "languages": {"Python": 0.7, "C++": 0.3},
                "top_repos": [{"name": "ml-lib", "stars": 5000}],
            }
        ],
        "total_found": 1,
    }

    with patch("khire.routers.search.PlannerAgent") as MockPlanner:
        instance = MockPlanner.return_value
        instance.search = AsyncMock(return_value=mock_search_result)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/search", json={"query": "Find ML engineers"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] == 1
    assert data["candidates"][0]["username"] == "ml_expert"
    assert data["candidates"][0]["overall_score"] == 0.85


@pytest.mark.asyncio
async def test_search_endpoint_empty_results():
    mock_search_result = {
        "query": "Find unicorn developers",
        "intent": {"search_queries": ["unicorn"], "required_skills": [], "min_stars": 0, "role_type": "unknown", "keywords": []},
        "candidates": [],
        "total_found": 0,
    }

    with patch("khire.routers.search.PlannerAgent") as MockPlanner:
        instance = MockPlanner.return_value
        instance.search = AsyncMock(return_value=mock_search_result)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/search", json={"query": "Find unicorn developers"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] == 0
    assert data["candidates"] == []


@pytest.mark.asyncio
async def test_search_endpoint_requires_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/search", json={})

    assert resp.status_code == 422  # Validation error
