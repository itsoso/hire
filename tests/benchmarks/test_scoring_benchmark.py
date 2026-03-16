"""
Benchmark tests to verify scoring produces sensible results.
Uses synthetic fixtures modeled after known developer archetypes.
"""
import pytest

from khire.agents.github_agent import GitHubAgent


@pytest.fixture
def agent():
    return GitHubAgent.__new__(GitHubAgent)


class TestRepoInfluenceScoring:
    def test_mega_popular_repo(self, agent):
        repo = {"stargazers_count": 125000, "forks_count": 25000, "fork": False}
        assert agent._score_repo_influence(repo) >= 0.9

    def test_popular_repo(self, agent):
        repo = {"stargazers_count": 5000, "forks_count": 800, "fork": False}
        score = agent._score_repo_influence(repo)
        assert 0.6 <= score <= 0.95

    def test_small_project(self, agent):
        repo = {"stargazers_count": 30, "forks_count": 5, "fork": False}
        score = agent._score_repo_influence(repo)
        assert score < 0.5

    def test_new_empty_repo(self, agent):
        repo = {"stargazers_count": 0, "forks_count": 0, "fork": False}
        score = agent._score_repo_influence(repo)
        assert score == 0.0


class TestPRClassification:
    def test_large_feature_pr(self, agent):
        pr = {"title": "Implement distributed training pipeline", "additions": 800, "deletions": 100, "changed_files": 15, "merged": True}
        assert agent._classify_pr(pr) == "core_feature"

    def test_medium_bugfix(self, agent):
        pr = {"title": "Fix memory leak in data loader", "additions": 80, "deletions": 20, "changed_files": 3, "merged": True}
        assert agent._classify_pr(pr) == "significant"

    def test_readme_update(self, agent):
        pr = {"title": "Update README with new examples", "additions": 3, "deletions": 2, "changed_files": 1, "merged": True}
        assert agent._classify_pr(pr) == "trivial"


class TestOverallScoring:
    def test_strong_developer_archetype(self, agent):
        metrics = {
            "repo_influence": 0.95,
            "pr_quality": 0.8,
            "collaboration": 0.7,
            "consistency": 0.9,
            "language_diversity": 0.6,
        }
        score = agent._compute_overall_score(metrics)
        assert score >= 0.8

    def test_junior_developer_archetype(self, agent):
        metrics = {
            "repo_influence": 0.1,
            "pr_quality": 0.1,
            "collaboration": 0.0,
            "consistency": 0.3,
            "language_diversity": 0.2,
        }
        score = agent._compute_overall_score(metrics)
        assert score < 0.2

    def test_score_ordering(self, agent):
        strong = {"repo_influence": 0.9, "pr_quality": 0.8, "collaboration": 0.7, "consistency": 0.8, "language_diversity": 0.6}
        junior = {"repo_influence": 0.1, "pr_quality": 0.1, "collaboration": 0.0, "consistency": 0.3, "language_diversity": 0.2}
        assert agent._compute_overall_score(strong) > agent._compute_overall_score(junior)
