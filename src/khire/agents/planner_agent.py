from __future__ import annotations

import asyncio

from khire.agents.github_agent import GitHubAgent
from khire.clients.github import GitHubClient
from khire.llm import LLMClient


class PlannerAgent:
    """Orchestrator that parses search intent and coordinates sub-agents."""

    def __init__(self, llm: LLMClient | None = None, github_client: GitHubClient | None = None):
        self.llm = llm or LLMClient()
        self.gh = github_client or GitHubClient()
        self.github_agent = GitHubAgent(github_client=self.gh, llm=self.llm)

    async def parse_intent(self, query: str) -> dict:
        """Use LLM to parse a natural language search query into structured intent."""
        prompt = f"""Parse this recruiting search query into structured JSON.

Query: "{query}"

Return a JSON object with these fields:
- "search_queries": list of 1-3 GitHub search query strings to find matching users
- "required_skills": list of programming languages or technologies the candidate must know
- "min_stars": minimum total stars across repos (0 if not specified)
- "role_type": one of "researcher", "engineer", "fullstack", "ml_engineer", "data_scientist", "devops", "unknown"
- "keywords": list of important keywords extracted from the query

Return ONLY valid JSON, no markdown."""

        return await self.llm.complete_json(
            prompt,
            system="You are an AI recruiting assistant that parses job search queries.",
        )

    async def search(self, query: str) -> dict:
        """Full search pipeline: parse intent -> find candidates -> analyze -> rank."""
        # Step 1: Parse intent
        intent = await self.parse_intent(query)

        # Step 2: Search GitHub for candidates
        search_queries = intent.get("search_queries", [query])
        all_candidates: dict[str, dict] = {}

        for sq in search_queries[:3]:
            users = await self.gh.search_users(sq)
            for user in users:
                login = user.get("login", "")
                if login and login not in all_candidates:
                    all_candidates[login] = user

        if not all_candidates:
            return {
                "query": query,
                "intent": intent,
                "candidates": [],
                "total_found": 0,
            }

        # Step 3: Analyze top candidates (limit to 10 to avoid rate limits)
        candidate_logins = list(all_candidates.keys())[:10]
        analyses = await asyncio.gather(
            *[self._safe_analyze(login) for login in candidate_logins],
            return_exceptions=True,
        )

        # Step 4: Filter and rank
        results = []
        required_skills = {s.lower() for s in intent.get("required_skills", [])}
        min_stars = intent.get("min_stars", 0)

        for analysis in analyses:
            if isinstance(analysis, Exception) or analysis is None:
                continue

            # Filter by required skills
            candidate_langs = {lang.lower() for lang in analysis.get("languages", {})}
            if required_skills and not required_skills.intersection(candidate_langs):
                continue

            # Filter by min stars
            top_stars = max((r.get("stars", 0) for r in analysis.get("top_repos", [{}])), default=0)
            if top_stars < min_stars:
                continue

            results.append(analysis)

        # Sort by overall score descending
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        return {
            "query": query,
            "intent": intent,
            "candidates": results,
            "total_found": len(results),
        }

    async def _safe_analyze(self, username: str) -> dict | None:
        """Analyze a user, returning None on failure."""
        try:
            return await self.github_agent.analyze(username)
        except Exception:
            return None
