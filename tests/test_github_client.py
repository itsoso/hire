import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from khire.clients.github import GitHubClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_get_user():
    user_data = load_fixture("github_user.json")
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=user_data)
    )

    client = GitHubClient(token="fake-token")
    user = await client.get_user("testuser")

    assert user["login"] == "testuser"
    assert user["followers"] == 1500


@respx.mock
@pytest.mark.asyncio
async def test_get_repos():
    repos_data = load_fixture("github_repos.json")
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=repos_data)
    )

    client = GitHubClient(token="fake-token")
    repos = await client.get_repos("testuser")

    assert len(repos) == 2
    assert repos[0]["stargazers_count"] == 3200


@respx.mock
@pytest.mark.asyncio
async def test_get_events():
    events_data = load_fixture("github_events.json")
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=events_data)
    )

    client = GitHubClient(token="fake-token")
    events = await client.get_events("testuser")

    assert len(events) == 3
    assert events[0]["type"] == "PullRequestEvent"


@respx.mock
@pytest.mark.asyncio
async def test_get_user_not_found():
    respx.get("https://api.github.com/users/nobody99999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    client = GitHubClient(token="fake-token")
    with pytest.raises(ValueError, match="not found"):
        await client.get_user("nobody99999")
