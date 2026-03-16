import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from khire.agents.planner_agent import PlannerAgent
from khire.clients.github import GitHubClient
from khire.llm import LLMClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.asyncio
async def test_parse_intent():
    mock_llm = LLMClient.__new__(LLMClient)
    mock_llm.complete_json = AsyncMock(return_value={
        "search_queries": ["machine learning pytorch language:python"],
        "required_skills": ["python", "pytorch"],
        "min_stars": 100,
        "role_type": "ml_engineer",
        "keywords": ["machine learning", "pytorch", "deep learning"],
    })

    planner = PlannerAgent(llm=mock_llm)
    intent = await planner.parse_intent("Find ML engineers who know PyTorch")

    assert "search_queries" in intent
    assert "required_skills" in intent
    assert intent["role_type"] == "ml_engineer"


@pytest.mark.asyncio
async def test_search_returns_ranked_candidates():
    mock_llm = LLMClient.__new__(LLMClient)
    mock_llm.complete_json = AsyncMock(return_value={
        "search_queries": ["machine learning language:python"],
        "required_skills": ["python"],
        "min_stars": 0,
        "role_type": "ml_engineer",
        "keywords": ["ml"],
    })

    mock_gh = GitHubClient.__new__(GitHubClient)
    mock_gh.search_users = AsyncMock(return_value=[
        {"login": "user_a"},
        {"login": "user_b"},
    ])

    # Mock the GitHub agent's analyze to return different scores
    planner = PlannerAgent(llm=mock_llm, github_client=mock_gh)

    async def mock_analyze(username):
        scores = {"user_a": 0.9, "user_b": 0.6}
        return {
            "username": username,
            "user_info": {"name": username, "bio": "", "company": "", "location": "", "followers": 0},
            "metrics": {"repo_influence": scores[username], "pr_quality": 0.5, "collaboration": 0.5, "consistency": 0.5, "language_diversity": 0.5},
            "overall_score": scores[username],
            "languages": {"Python": 1.0},
            "top_repos": [{"name": "repo1", "stars": 100}],
            "pr_count": 5,
            "external_pr_count": 2,
        }

    planner.github_agent.analyze = mock_analyze

    result = await planner.search("Find ML engineers")

    assert result["total_found"] == 2
    assert result["candidates"][0]["username"] == "user_a"  # Higher score first
    assert result["candidates"][0]["overall_score"] > result["candidates"][1]["overall_score"]


@pytest.mark.asyncio
async def test_search_filters_by_required_skills():
    mock_llm = LLMClient.__new__(LLMClient)
    mock_llm.complete_json = AsyncMock(return_value={
        "search_queries": ["rust developer"],
        "required_skills": ["rust"],
        "min_stars": 0,
        "role_type": "engineer",
        "keywords": ["rust"],
    })

    mock_gh = GitHubClient.__new__(GitHubClient)
    mock_gh.search_users = AsyncMock(return_value=[
        {"login": "rust_dev"},
        {"login": "python_dev"},
    ])

    planner = PlannerAgent(llm=mock_llm, github_client=mock_gh)

    async def mock_analyze(username):
        langs = {"rust_dev": {"Rust": 0.8}, "python_dev": {"Python": 1.0}}
        return {
            "username": username,
            "user_info": {"name": username, "bio": "", "company": "", "location": "", "followers": 0},
            "metrics": {"repo_influence": 0.5, "pr_quality": 0.5, "collaboration": 0.5, "consistency": 0.5, "language_diversity": 0.5},
            "overall_score": 0.5,
            "languages": langs[username],
            "top_repos": [{"name": "repo1", "stars": 100}],
            "pr_count": 5,
            "external_pr_count": 2,
        }

    planner.github_agent.analyze = mock_analyze

    result = await planner.search("Find Rust developers")

    assert result["total_found"] == 1
    assert result["candidates"][0]["username"] == "rust_dev"


@pytest.mark.asyncio
async def test_search_empty_results():
    mock_llm = LLMClient.__new__(LLMClient)
    mock_llm.complete_json = AsyncMock(return_value={
        "search_queries": ["nonexistent skill xyz"],
        "required_skills": [],
        "min_stars": 0,
        "role_type": "unknown",
        "keywords": [],
    })

    mock_gh = GitHubClient.__new__(GitHubClient)
    mock_gh.search_users = AsyncMock(return_value=[])

    planner = PlannerAgent(llm=mock_llm, github_client=mock_gh)
    result = await planner.search("Find developers with nonexistent skill")

    assert result["total_found"] == 0
    assert result["candidates"] == []


@pytest.mark.asyncio
async def test_search_handles_analyze_failures_gracefully():
    mock_llm = LLMClient.__new__(LLMClient)
    mock_llm.complete_json = AsyncMock(return_value={
        "search_queries": ["python developer"],
        "required_skills": [],
        "min_stars": 0,
        "role_type": "engineer",
        "keywords": ["python"],
    })

    mock_gh = GitHubClient.__new__(GitHubClient)
    mock_gh.search_users = AsyncMock(return_value=[
        {"login": "good_user"},
        {"login": "bad_user"},
    ])

    planner = PlannerAgent(llm=mock_llm, github_client=mock_gh)

    async def mock_analyze(username):
        if username == "bad_user":
            raise ValueError("API error")
        return {
            "username": username,
            "user_info": {"name": username, "bio": "", "company": "", "location": "", "followers": 0},
            "metrics": {"repo_influence": 0.7, "pr_quality": 0.5, "collaboration": 0.5, "consistency": 0.5, "language_diversity": 0.5},
            "overall_score": 0.7,
            "languages": {"Python": 1.0},
            "top_repos": [{"name": "repo1", "stars": 500}],
            "pr_count": 10,
            "external_pr_count": 3,
        }

    planner.github_agent.analyze = mock_analyze

    result = await planner.search("Find Python developers")

    # Should still return the good user, gracefully skipping the bad one
    assert result["total_found"] == 1
    assert result["candidates"][0]["username"] == "good_user"
