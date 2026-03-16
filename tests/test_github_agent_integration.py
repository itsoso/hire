import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from khire.agents.github_agent import GitHubAgent
from khire.clients.github import GitHubClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_github_agent_full_analyze():
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=load_fixture("github_user.json"))
    )
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=load_fixture("github_repos.json"))
    )
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=load_fixture("github_events.json"))
    )

    client = GitHubClient(token="fake")
    agent = GitHubAgent(github_client=client)
    result = await agent.analyze("testuser")

    assert result["username"] == "testuser"
    assert result["user_info"]["name"] == "Test User"
    assert "Python" in result["languages"]
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["metrics"]["repo_influence"] > 0
    assert len(result["top_repos"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_github_agent_user_not_found():
    respx.get("https://api.github.com/users/nonexistent").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    client = GitHubClient(token="fake")
    agent = GitHubAgent(github_client=client)

    with pytest.raises(ValueError, match="not found"):
        await agent.analyze("nonexistent")
