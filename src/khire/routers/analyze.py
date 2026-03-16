from __future__ import annotations

from fastapi import APIRouter, HTTPException

from khire.agents.github_agent import GitHubAgent
from khire.llm import LLMClient

router = APIRouter(prefix="/api")


@router.post("/analyze/{github_username}")
async def analyze_user(github_username: str):
    agent = GitHubAgent()

    try:
        analysis = await agent.analyze(github_username)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"GitHub user '{github_username}' not found")

    llm = LLMClient()
    prompt = f"""Based on this GitHub analysis, write a 2-3 sentence professional summary:

Username: {analysis['username']}
Top repos: {analysis['top_repos'][:5]}
Languages: {analysis['languages']}
Metrics: {analysis['metrics']}
Overall score: {analysis['overall_score']}
Bio: {analysis['user_info'].get('bio', 'N/A')}

Return ONLY the summary text, no JSON."""

    try:
        summary = await llm.complete(prompt, system="You are a technical recruiter AI.")
    except Exception:
        summary = ""

    return {
        "github_username": github_username,
        "profile_summary": summary,
        "skill_tags": list(analysis["languages"].keys()),
        "overall_score": analysis["overall_score"],
        "metrics": analysis["metrics"],
        "top_repos": analysis["top_repos"],
        "languages": analysis["languages"],
        "user_info": analysis["user_info"],
    }
