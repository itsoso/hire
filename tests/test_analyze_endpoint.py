import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from khire.main import app

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_analyze_returns_profile():
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=load_fixture("github_user.json"))
    )
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=load_fixture("github_repos.json"))
    )
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=load_fixture("github_events.json"))
    )

    with patch("khire.routers.analyze.LLMClient") as MockLLM:
        instance = MockLLM.return_value
        instance.complete = AsyncMock(return_value="Strong ML engineer with open source contributions.")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/analyze/testuser")

    assert resp.status_code == 200
    data = resp.json()
    assert data["github_username"] == "testuser"
    assert "skill_tags" in data
    assert data["overall_score"] > 0
    assert "metrics" in data
    assert len(data["top_repos"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_analyze_user_not_found():
    respx.get("https://api.github.com/users/nobody99999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/analyze/nobody99999")

    assert resp.status_code == 404
