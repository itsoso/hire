import pytest

from khire.agents.network_agent import NetworkAgent


@pytest.mark.asyncio
async def test_build_network_from_events():
    events = [
        {
            "type": "PullRequestEvent",
            "repo": {"name": "huggingface/transformers"},
            "payload": {
                "action": "closed",
                "pull_request": {"merged": True, "title": "Add feature"},
            },
        },
        {
            "type": "PullRequestEvent",
            "repo": {"name": "huggingface/transformers"},
            "payload": {
                "action": "opened",
                "pull_request": {"title": "Another PR"},
            },
        },
        {
            "type": "IssuesEvent",
            "repo": {"name": "pytorch/pytorch"},
            "payload": {"action": "opened"},
        },
    ]

    agent = NetworkAgent.__new__(NetworkAgent)
    result = await agent.build_network("testuser", events=events)

    assert result["username"] == "testuser"
    assert result["total_connections"] == 2

    # huggingface should have strength >= pytorch (2 interactions vs 1)
    hf = next((c for c in result["connections"] if c["username"] == "huggingface"), None)
    pt = next((c for c in result["connections"] if c["username"] == "pytorch"), None)
    assert hf is not None
    assert pt is not None
    assert hf["interaction_count"] >= pt["interaction_count"]


@pytest.mark.asyncio
async def test_build_network_excludes_self():
    events = [
        {
            "type": "PullRequestEvent",
            "repo": {"name": "testuser/my-repo"},
            "payload": {
                "action": "closed",
                "pull_request": {"merged": True, "title": "Self PR"},
            },
        },
    ]

    agent = NetworkAgent.__new__(NetworkAgent)
    result = await agent.build_network("testuser", events=events)

    # Should not include self as a connection
    assert all(c["username"] != "testuser" for c in result["connections"])


@pytest.mark.asyncio
async def test_build_network_empty_events():
    agent = NetworkAgent.__new__(NetworkAgent)
    result = await agent.build_network("testuser", events=[])

    assert result["connections"] == []
    assert result["total_connections"] == 0


@pytest.mark.asyncio
async def test_network_strength_calculation():
    # 5+ interactions should give strength 1.0
    events = [
        {
            "type": "PullRequestEvent",
            "repo": {"name": "org/repo"},
            "payload": {"action": "closed", "pull_request": {"merged": True, "title": f"PR {i}"}},
        }
        for i in range(6)
    ]

    agent = NetworkAgent.__new__(NetworkAgent)
    result = await agent.build_network("testuser", events=events)

    org_conn = next((c for c in result["connections"] if c["username"] == "org"), None)
    assert org_conn is not None
    assert org_conn["strength"] == 1.0
