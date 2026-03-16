from __future__ import annotations

import math
import re

from khire.clients.github import GitHubClient
from khire.llm import LLMClient


class GitHubAgent:
    def __init__(self, github_client: GitHubClient | None = None, llm: LLMClient | None = None):
        self.gh = github_client or GitHubClient()
        self.llm = llm or LLMClient()

    async def analyze(self, username: str) -> dict:
        user = await self.gh.get_user(username)
        repos = await self.gh.get_repos(username)
        events = await self.gh.get_events(username)

        owned_repos = [r for r in repos if not r.get("fork")]
        pr_events = [
            e for e in events
            if e.get("type") == "PullRequestEvent"
            and e.get("payload", {}).get("pull_request", {}).get("merged")
        ]

        repo_scores = [self._score_repo_influence(r) for r in owned_repos] or [0]
        repo_influence = max(repo_scores)

        pr_qualities = [self._classify_pr(e["payload"]["pull_request"]) for e in pr_events]
        pr_quality = self._score_pr_quality(pr_qualities)

        languages = self._detect_languages(repos)
        language_diversity = min(len(languages) / 5, 1.0)

        consistency = min(len(events) / 30, 1.0)

        external_prs = [
            e for e in pr_events
            if not e["repo"]["name"].startswith(f"{username}/")
        ]
        collaboration = min(len(external_prs) / 5, 1.0)

        metrics = {
            "repo_influence": repo_influence,
            "pr_quality": pr_quality,
            "language_diversity": language_diversity,
            "consistency": consistency,
            "collaboration": collaboration,
        }

        return {
            "username": username,
            "user_info": {
                "name": user.get("name"),
                "bio": user.get("bio"),
                "company": user.get("company"),
                "location": user.get("location"),
                "followers": user.get("followers", 0),
            },
            "metrics": metrics,
            "overall_score": self._compute_overall_score(metrics),
            "languages": languages,
            "top_repos": sorted(
                [{"name": r["name"], "stars": r.get("stargazers_count", 0)} for r in owned_repos],
                key=lambda r: r["stars"],
                reverse=True,
            )[:10],
            "pr_count": len(pr_events),
            "external_pr_count": len(external_prs),
        }

    def _score_repo_influence(self, repo: dict) -> float:
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        is_fork = repo.get("fork", False)

        raw = math.log10(max(stars + forks * 0.5, 1)) / 4.5
        score = min(max(raw, 0.0), 1.0)

        if is_fork:
            score *= 0.5

        return score

    def _classify_pr(self, pr: dict) -> str:
        title = (pr.get("title") or "").lower()
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        changed_files = pr.get("changed_files", 0)
        total_changes = additions + deletions

        trivial_patterns = r"(typo|readme|docs?[ _-]fix|fix.*typo|spelling)"
        if re.search(trivial_patterns, title) or (total_changes <= 5 and changed_files <= 1):
            return "trivial"

        if total_changes > 200 and changed_files > 5:
            return "core_feature"

        if total_changes > 50:
            return "significant"

        return "minor"

    def _score_pr_quality(self, qualities: list[str]) -> float:
        if not qualities:
            return 0.0
        weights = {"core_feature": 1.0, "significant": 0.7, "minor": 0.3, "trivial": 0.05}
        total = sum(weights.get(q, 0) for q in qualities)
        return min(total / 3, 1.0)

    def _detect_languages(self, repos: list[dict]) -> dict[str, float]:
        counts: dict[str, int] = {}
        total = 0
        for r in repos:
            lang = r.get("language")
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
                total += 1
        if total == 0:
            return {}
        return {lang: round(count / total, 2) for lang, count in counts.items()}

    def _compute_overall_score(self, metrics: dict) -> float:
        weights = {
            "repo_influence": 0.30,
            "pr_quality": 0.30,
            "collaboration": 0.20,
            "consistency": 0.10,
            "language_diversity": 0.10,
        }
        return round(sum(metrics.get(k, 0) * w for k, w in weights.items()), 3)
