from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter

from khire.agents.planner_agent import PlannerAgent

router = APIRouter(prefix="/api")


class SearchRequest(BaseModel):
    query: str


class CandidateResponse(BaseModel):
    username: str
    overall_score: float
    user_info: dict
    metrics: dict
    languages: dict
    top_repos: list


class SearchResponse(BaseModel):
    query: str
    intent: dict
    candidates: list[CandidateResponse]
    total_found: int


@router.post("/search", response_model=SearchResponse)
async def search_candidates(request: SearchRequest):
    planner = PlannerAgent()
    result = await planner.search(request.query)

    candidates = [
        CandidateResponse(
            username=c["username"],
            overall_score=c.get("overall_score", 0),
            user_info=c.get("user_info", {}),
            metrics=c.get("metrics", {}),
            languages=c.get("languages", {}),
            top_repos=c.get("top_repos", []),
        )
        for c in result["candidates"]
    ]

    return SearchResponse(
        query=result["query"],
        intent=result["intent"],
        candidates=candidates,
        total_found=result["total_found"],
    )
