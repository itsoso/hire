from __future__ import annotations

from fastapi import APIRouter, HTTPException

from khire.agents.github_agent import GitHubAgent
from khire.agents.network_agent import NetworkAgent
from khire.agents.scholar_agent import ScholarAgent
from khire.llm import LLMClient

router = APIRouter(prefix="/api")


@router.get("/developer/{github_username}")
async def get_developer(github_username: str):
    """Get full developer profile with GitHub analysis and optional scholar data."""
    gh_agent = GitHubAgent()

    try:
        analysis = await gh_agent.analyze(github_username)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"GitHub user '{github_username}' not found")

    # Generate LLM summary
    llm = LLMClient()
    try:
        summary = await llm.complete(
            f"""Write a 2-3 sentence professional profile for this developer:
Name: {analysis['user_info'].get('name', github_username)}
Bio: {analysis['user_info'].get('bio', 'N/A')}
Top languages: {list(analysis['languages'].keys())[:5]}
Top repos: {[r['name'] for r in analysis['top_repos'][:3]]}
Score: {analysis['overall_score']}
Return ONLY the summary text.""",
            system="You are a technical recruiter AI.",
        )
    except Exception:
        summary = ""

    return {
        "github_username": github_username,
        "profile_summary": summary,
        "user_info": analysis["user_info"],
        "overall_score": analysis["overall_score"],
        "metrics": analysis["metrics"],
        "languages": analysis["languages"],
        "top_repos": analysis["top_repos"],
        "pr_count": analysis["pr_count"],
        "external_pr_count": analysis["external_pr_count"],
    }


@router.get("/developer/{github_username}/network")
async def get_developer_network(github_username: str):
    """Get collaboration network for a developer."""
    network_agent = NetworkAgent()

    try:
        network = await network_agent.build_network(github_username)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"GitHub user '{github_username}' not found")

    return network


@router.get("/developer/{github_username}/scholar")
async def get_developer_scholar(github_username: str, author_name: str | None = None):
    """Get academic profile. Uses author_name query param or GitHub display name."""
    if not author_name:
        gh_agent = GitHubAgent()
        try:
            analysis = await gh_agent.analyze(github_username)
            author_name = analysis["user_info"].get("name") or github_username
        except ValueError:
            raise HTTPException(status_code=404, detail=f"GitHub user '{github_username}' not found")

    scholar_agent = ScholarAgent()
    return await scholar_agent.analyze(author_name)
