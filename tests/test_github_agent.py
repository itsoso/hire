import pytest

from khire.agents.github_agent import GitHubAgent


def test_score_repo_influence_high_stars():
    agent = GitHubAgent.__new__(GitHubAgent)
    repo = {"stargazers_count": 10000, "forks_count": 2000, "fork": False}
    score = agent._score_repo_influence(repo)
    assert 0.8 <= score <= 1.0


def test_score_repo_influence_low_stars():
    agent = GitHubAgent.__new__(GitHubAgent)
    repo = {"stargazers_count": 5, "forks_count": 0, "fork": False}
    score = agent._score_repo_influence(repo)
    assert 0.0 <= score <= 0.3


def test_score_repo_influence_fork_penalty():
    agent = GitHubAgent.__new__(GitHubAgent)
    owned = {"stargazers_count": 100, "forks_count": 20, "fork": False}
    forked = {"stargazers_count": 100, "forks_count": 20, "fork": True}
    assert agent._score_repo_influence(owned) > agent._score_repo_influence(forked)


def test_classify_pr_quality_high():
    agent = GitHubAgent.__new__(GitHubAgent)
    pr = {
        "title": "Add FlashAttention-2 support for Llama",
        "additions": 500,
        "deletions": 50,
        "changed_files": 12,
        "merged": True,
    }
    quality = agent._classify_pr(pr)
    assert quality in ("core_feature", "significant")


def test_classify_pr_quality_doc_fix():
    agent = GitHubAgent.__new__(GitHubAgent)
    pr = {
        "title": "Fix typo in README.md",
        "additions": 1,
        "deletions": 1,
        "changed_files": 1,
        "merged": True,
    }
    quality = agent._classify_pr(pr)
    assert quality == "trivial"


def test_detect_languages():
    agent = GitHubAgent.__new__(GitHubAgent)
    repos = [
        {"language": "Python"},
        {"language": "Python"},
        {"language": "Rust"},
        {"language": None},
    ]
    langs = agent._detect_languages(repos)
    assert langs["Python"] == pytest.approx(0.67, abs=0.01)
    assert langs["Rust"] == pytest.approx(0.33, abs=0.01)


def test_compute_overall_score():
    agent = GitHubAgent.__new__(GitHubAgent)
    metrics = {
        "repo_influence": 0.8,
        "pr_quality": 0.7,
        "language_diversity": 0.5,
        "consistency": 0.9,
        "collaboration": 0.6,
    }
    score = agent._compute_overall_score(metrics)
    assert 0.0 <= score <= 1.0
    assert score > 0.6
