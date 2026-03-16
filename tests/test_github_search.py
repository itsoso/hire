import pytest
import respx
from httpx import Response

from khire.clients.github import GitHubClient


@respx.mock
@pytest.mark.asyncio
async def test_search_users():
    respx.get("https://api.github.com/search/users").mock(
        return_value=Response(200, json={
            "total_count": 2,
            "items": [
                {"login": "user1", "id": 1},
                {"login": "user2", "id": 2},
            ]
        })
    )

    client = GitHubClient(token="fake")
    users = await client.search_users("machine learning language:python")

    assert len(users) == 2
    assert users[0]["login"] == "user1"


@respx.mock
@pytest.mark.asyncio
async def test_search_users_empty():
    respx.get("https://api.github.com/search/users").mock(
        return_value=Response(200, json={
            "total_count": 0,
            "items": []
        })
    )

    client = GitHubClient(token="fake")
    users = await client.search_users("nonexistent xyz")

    assert users == []
