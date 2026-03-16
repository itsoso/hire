import pytest
from khire.models import Developer, SearchQuery


def test_developer_model_fields():
    dev = Developer(
        github_username="karpathy",
        github_data={"repos": [], "languages": {"python": 80}},
        skill_tags=["ml", "python"],
        overall_score=0.95,
    )
    assert dev.github_username == "karpathy"
    assert dev.github_data["languages"]["python"] == 80
    assert dev.overall_score == 0.95


def test_search_query_model_fields():
    sq = SearchQuery(
        query_text="find LLM infra engineers",
        parsed_intent={"role": "infra", "domain": "llm"},
    )
    assert sq.query_text == "find LLM infra engineers"
    assert sq.parsed_intent["role"] == "infra"
