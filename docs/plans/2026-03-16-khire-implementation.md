# KHire Implementation Plan — Phase 1 & 2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the backend infrastructure and GitHub analysis engine for a talent recruitment platform that evaluates developers by their actual GitHub contributions.

**Architecture:** FastAPI backend with Agent orchestration. Each agent (GitHub, Scholar, Social, Ranking) is a standalone async class orchestrated by a Planner. LLM calls go through LiteLLM so we can swap Claude/GPT/DeepSeek. PostgreSQL stores developer profiles; Redis caches GitHub API responses.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), LiteLLM, httpx, pytest, PostgreSQL, Redis, Docker Compose

---

## Phase 1: Infrastructure

### Task 1: Project Scaffold & Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/khire/__init__.py`
- Create: `src/khire/main.py`
- Create: `src/khire/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `docker-compose.yml`
- Create: `.env.example`

**Step 1: Create `pyproject.toml` with all dependencies**

```toml
[project]
name = "khire"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "redis>=5.0.0",
    "httpx>=0.28.0",
    "litellm>=1.55.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-httpx>=0.35.0",
    "respx>=0.22.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100
```

**Step 2: Create `src/khire/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://khire:khire@localhost:5432/khire"
    redis_url: str = "redis://localhost:6379/0"
    github_token: str = ""
    default_llm_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

**Step 3: Create `src/khire/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="KHire", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Create `src/khire/__init__.py`**

```python
```

**Step 5: Create `.env.example`**

```
DATABASE_URL=postgresql+asyncpg://khire:khire@localhost:5432/khire
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=ghp_your_token_here
DEFAULT_LLM_MODEL=gpt-4o-mini
```

**Step 6: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: khire
      POSTGRES_PASSWORD: khire
      POSTGRES_DB: khire
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

**Step 7: Create `tests/__init__.py` and `tests/conftest.py`**

`tests/__init__.py`: empty file

`tests/conftest.py`:
```python
import pytest
from httpx import ASGITransport, AsyncClient

from khire.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

**Step 8: Install and verify**

Run:
```bash
cd /Users/liqiuhua/work/personal/KHire
pip install -e ".[dev]"
```
Expected: installs without errors

**Step 9: Commit**

```bash
git add -A
git commit -m "feat: project scaffold with FastAPI, config, docker-compose"
```

---

### Task 2: Health Endpoint Test (TDD warmup)

**Files:**
- Create: `tests/test_health.py`

**Step 1: Write the failing test**

```python
import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
```

**Step 2: Run test to verify it passes** (it should pass since we already wrote the endpoint)

Run: `pytest tests/test_health.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_health.py
git commit -m "test: add health endpoint test"
```

---

### Task 3: Database Models

**Files:**
- Create: `src/khire/models.py`
- Create: `src/khire/database.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

`tests/test_models.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'khire.models'`

**Step 3: Create `src/khire/database.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from khire.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**Step 4: Create `src/khire/models.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    github_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    scholar_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    social_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_tags: Mapped[list] = mapped_column(JSONB, default=list)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    network: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query_text: Mapped[str] = mapped_column(Text)
    parsed_intent: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[list] = mapped_column(JSONB, default=list)
    employer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (tests only check in-memory model construction, no DB needed)

**Step 6: Commit**

```bash
git add src/khire/models.py src/khire/database.py tests/test_models.py
git commit -m "feat: add Developer and SearchQuery SQLAlchemy models"
```

---

### Task 4: LLM Abstraction Layer

**Files:**
- Create: `src/khire/llm.py`
- Create: `tests/test_llm.py`

**Step 1: Write the failing test**

`tests/test_llm.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch

from khire.llm import LLMClient


@pytest.mark.asyncio
async def test_llm_client_complete():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": "Hello from LLM"})()})()
        ]

        client = LLMClient(model="gpt-4o-mini")
        result = await client.complete("Say hello")

        assert result == "Hello from LLM"
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_llm_client_complete_json():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": '{"key": "value"}'})()})()
        ]

        client = LLMClient(model="gpt-4o-mini")
        result = await client.complete_json("Return JSON")

        assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_llm_client_switches_model():
    with patch("khire.llm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": "ok"})()})()
        ]

        client = LLMClient(model="claude-sonnet-4-20250514")
        await client.complete("test")

        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-20250514"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'khire.llm'`

**Step 3: Implement `src/khire/llm.py`**

```python
from __future__ import annotations

import json

from litellm import acompletion

from khire.config import settings


class LLMClient:
    def __init__(self, model: str | None = None):
        self.model = model or settings.default_llm_model

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> dict:
        raw = await self.complete(prompt, system=system, temperature=temperature)
        return json.loads(raw)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_llm.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/khire/llm.py tests/test_llm.py
git commit -m "feat: add LLM abstraction layer via LiteLLM"
```

---

### Task 5: GitHub API Client

**Files:**
- Create: `src/khire/clients/__init__.py`
- Create: `src/khire/clients/github.py`
- Create: `tests/test_github_client.py`
- Create: `tests/fixtures/github_user.json`
- Create: `tests/fixtures/github_repos.json`
- Create: `tests/fixtures/github_events.json`

**Step 1: Create test fixtures**

`tests/fixtures/github_user.json`:
```json
{
  "login": "testuser",
  "name": "Test User",
  "bio": "ML engineer building cool stuff",
  "public_repos": 42,
  "followers": 1500,
  "following": 200,
  "created_at": "2018-01-15T00:00:00Z",
  "company": "OpenAI",
  "location": "San Francisco",
  "blog": "https://testuser.dev",
  "twitter_username": "testuser"
}
```

`tests/fixtures/github_repos.json`:
```json
[
  {
    "name": "awesome-ml",
    "full_name": "testuser/awesome-ml",
    "description": "Machine learning toolkit",
    "stargazers_count": 3200,
    "forks_count": 450,
    "language": "Python",
    "fork": false,
    "topics": ["machine-learning", "pytorch"],
    "created_at": "2020-03-01T00:00:00Z",
    "updated_at": "2024-11-01T00:00:00Z"
  },
  {
    "name": "transformers",
    "full_name": "huggingface/transformers",
    "description": "State-of-the-art ML for PyTorch, TensorFlow, JAX",
    "stargazers_count": 125000,
    "forks_count": 25000,
    "language": "Python",
    "fork": true,
    "topics": ["nlp", "transformers", "pytorch"],
    "created_at": "2018-10-29T00:00:00Z",
    "updated_at": "2024-12-01T00:00:00Z"
  }
]
```

`tests/fixtures/github_events.json`:
```json
[
  {
    "type": "PullRequestEvent",
    "repo": {"name": "huggingface/transformers"},
    "payload": {
      "action": "closed",
      "pull_request": {
        "merged": true,
        "title": "Add FlashAttention-2 support for Llama",
        "additions": 450,
        "deletions": 30,
        "changed_files": 8
      }
    },
    "created_at": "2024-10-15T00:00:00Z"
  },
  {
    "type": "PushEvent",
    "repo": {"name": "testuser/awesome-ml"},
    "payload": {"size": 3},
    "created_at": "2024-10-14T00:00:00Z"
  },
  {
    "type": "IssuesEvent",
    "repo": {"name": "pytorch/pytorch"},
    "payload": {"action": "opened"},
    "created_at": "2024-10-13T00:00:00Z"
  }
]
```

**Step 2: Write the failing tests**

`tests/test_github_client.py`:
```python
import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from khire.clients.github import GitHubClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_get_user():
    user_data = load_fixture("github_user.json")
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=user_data)
    )

    client = GitHubClient(token="fake-token")
    user = await client.get_user("testuser")

    assert user["login"] == "testuser"
    assert user["followers"] == 1500


@respx.mock
@pytest.mark.asyncio
async def test_get_repos():
    repos_data = load_fixture("github_repos.json")
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=repos_data)
    )

    client = GitHubClient(token="fake-token")
    repos = await client.get_repos("testuser")

    assert len(repos) == 2
    assert repos[0]["stargazers_count"] == 3200


@respx.mock
@pytest.mark.asyncio
async def test_get_events():
    events_data = load_fixture("github_events.json")
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=events_data)
    )

    client = GitHubClient(token="fake-token")
    events = await client.get_events("testuser")

    assert len(events) == 3
    assert events[0]["type"] == "PullRequestEvent"


@respx.mock
@pytest.mark.asyncio
async def test_get_user_not_found():
    respx.get("https://api.github.com/users/nobody99999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    client = GitHubClient(token="fake-token")
    with pytest.raises(ValueError, match="not found"):
        await client.get_user("nobody99999")
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_github_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'khire.clients'`

**Step 4: Implement `src/khire/clients/__init__.py`**

```python
```

**Step 5: Implement `src/khire/clients/github.py`**

```python
from __future__ import annotations

import httpx

from khire.config import settings

GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}{path}",
                headers=self.headers,
                params=params or {},
            )
            if resp.status_code == 404:
                raise ValueError(f"GitHub resource not found: {path}")
            resp.raise_for_status()
            return resp.json()

    async def get_user(self, username: str) -> dict:
        return await self._get(f"/users/{username}")

    async def get_repos(
        self, username: str, per_page: int = 100, sort: str = "updated"
    ) -> list[dict]:
        return await self._get(
            f"/users/{username}/repos",
            params={"per_page": per_page, "sort": sort, "type": "all"},
        )

    async def get_events(self, username: str, per_page: int = 100) -> list[dict]:
        return await self._get(
            f"/users/{username}/events",
            params={"per_page": per_page},
        )
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_github_client.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add src/khire/clients/ tests/test_github_client.py tests/fixtures/
git commit -m "feat: add GitHub API client with user, repos, events endpoints"
```

---

### Task 6: Analyze Endpoint (wiring it together)

**Files:**
- Create: `src/khire/routers/__init__.py`
- Create: `src/khire/routers/analyze.py`
- Create: `tests/test_analyze_endpoint.py`
- Modify: `src/khire/main.py` (add router)

**Step 1: Write the failing test**

`tests/test_analyze_endpoint.py`:
```python
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from khire.main import app

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_analyze_returns_profile():
    # Mock GitHub API
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=load_fixture("github_user.json"))
    )
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=load_fixture("github_repos.json"))
    )
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=load_fixture("github_events.json"))
    )

    # Mock LLM
    with patch("khire.routers.analyze.LLMClient") as MockLLM:
        instance = MockLLM.return_value
        instance.complete_json = AsyncMock(return_value={
            "summary": "Strong ML engineer with HuggingFace contributions",
            "skill_tags": ["python", "pytorch", "transformers"],
            "overall_score": 0.85,
        })

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/analyze/testuser")

        assert resp.status_code == 200
        data = resp.json()
        assert data["github_username"] == "testuser"
        assert "skill_tags" in data
        assert data["overall_score"] > 0


@respx.mock
@pytest.mark.asyncio
async def test_analyze_user_not_found():
    respx.get("https://api.github.com/users/nobody99999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/analyze/nobody99999")

    assert resp.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_analyze_endpoint.py -v`
Expected: FAIL — 404 because route doesn't exist

**Step 3: Create `src/khire/routers/__init__.py`**

```python
```

**Step 4: Create `src/khire/routers/analyze.py`**

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from khire.clients.github import GitHubClient
from khire.llm import LLMClient

router = APIRouter(prefix="/api")


@router.post("/analyze/{github_username}")
async def analyze_user(github_username: str):
    gh = GitHubClient()

    try:
        user = await gh.get_user(github_username)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"GitHub user '{github_username}' not found")

    repos = await gh.get_repos(github_username)
    events = await gh.get_events(github_username)

    # Prepare context for LLM analysis
    owned_repos = [r for r in repos if not r.get("fork")]
    top_repos = sorted(owned_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]
    languages = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    pr_events = [e for e in events if e.get("type") == "PullRequestEvent"]

    github_data = {
        "user": {
            "login": user["login"],
            "name": user.get("name"),
            "bio": user.get("bio"),
            "company": user.get("company"),
            "location": user.get("location"),
            "followers": user.get("followers", 0),
            "public_repos": user.get("public_repos", 0),
        },
        "top_repos": [
            {
                "name": r["name"],
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language"),
                "topics": r.get("topics", []),
            }
            for r in top_repos
        ],
        "languages": languages,
        "recent_prs": len(pr_events),
        "contributed_to": list({e["repo"]["name"] for e in events if e["repo"]["name"] != f"{github_username}/{e['repo']['name'].split('/')[-1]}"}),
    }

    # LLM analysis
    llm = LLMClient()
    prompt = f"""Analyze this GitHub developer profile and return a JSON object with:
- "summary": a 2-3 sentence profile summary
- "skill_tags": list of 5-10 skill tags (lowercase)
- "overall_score": a float from 0.0 to 1.0 representing overall technical strength

GitHub data:
{github_data}

Return ONLY valid JSON, no markdown."""

    analysis = await llm.complete_json(prompt, system="You are a technical recruiter AI.")

    return {
        "github_username": github_username,
        "github_data": github_data,
        "profile_summary": analysis.get("summary", ""),
        "skill_tags": analysis.get("skill_tags", []),
        "overall_score": analysis.get("overall_score", 0.0),
    }
```

**Step 5: Update `src/khire/main.py` to include the router**

```python
from fastapi import FastAPI

from khire.routers.analyze import router as analyze_router

app = FastAPI(title="KHire", version="0.1.0")
app.include_router(analyze_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_analyze_endpoint.py -v`
Expected: PASS (2 tests)

**Step 7: Run ALL tests to make sure nothing is broken**

Run: `pytest -v`
Expected: ALL PASS

**Step 8: Commit**

```bash
git add src/khire/routers/ src/khire/main.py tests/test_analyze_endpoint.py
git commit -m "feat: add /api/analyze endpoint wiring GitHub client + LLM"
```

---

## Phase 2: GitHub Analysis Engine

### Task 7: GitHub Agent — Contribution Scorer

**Files:**
- Create: `src/khire/agents/__init__.py`
- Create: `src/khire/agents/base.py`
- Create: `src/khire/agents/github_agent.py`
- Create: `tests/test_github_agent.py`

**Step 1: Write the failing tests**

`tests/test_github_agent.py`:
```python
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
    # repo_influence and pr_quality should be weighted higher
    assert score > 0.6
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github_agent.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Create `src/khire/agents/__init__.py`**

```python
```

**Step 4: Create `src/khire/agents/base.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    task_id: str
    agent_type: str
    action: str
    payload: dict = field(default_factory=dict)
    result: dict | None = None
    status: str = "pending"
```

**Step 5: Create `src/khire/agents/github_agent.py`**

```python
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

        # Score dimensions
        repo_scores = [self._score_repo_influence(r) for r in owned_repos] or [0]
        repo_influence = max(repo_scores)

        pr_qualities = [self._classify_pr(e["payload"]["pull_request"]) for e in pr_events]
        pr_quality = self._score_pr_quality(pr_qualities)

        languages = self._detect_languages(repos)
        language_diversity = min(len(languages) / 5, 1.0)

        # Consistency: events spread over time
        consistency = min(len(events) / 30, 1.0)

        # Collaboration: PRs to repos you don't own
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

        # Log scale: 10 stars = ~0.33, 100 = ~0.67, 1000 = ~0.83, 10000 = ~1.0
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

        # Trivial: doc fixes, typos, very small changes
        trivial_patterns = r"(typo|readme|docs?[ _-]fix|fix.*typo|spelling)"
        if re.search(trivial_patterns, title) or (total_changes <= 5 and changed_files <= 1):
            return "trivial"

        # Core feature: large PRs with feature-like titles
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
        return min(total / 3, 1.0)  # 3 significant PRs = 1.0

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
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_github_agent.py -v`
Expected: PASS (7 tests)

**Step 7: Commit**

```bash
git add src/khire/agents/ tests/test_github_agent.py
git commit -m "feat: add GitHubAgent with contribution scoring algorithm"
```

---

### Task 8: GitHub Agent Integration Test

**Files:**
- Create: `tests/test_github_agent_integration.py`

This test verifies the full `GitHubAgent.analyze()` flow with mocked HTTP.

**Step 1: Write the test**

`tests/test_github_agent_integration.py`:
```python
import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from khire.agents.github_agent import GitHubAgent
from khire.clients.github import GitHubClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_github_agent_full_analyze():
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=load_fixture("github_user.json"))
    )
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=load_fixture("github_repos.json"))
    )
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=load_fixture("github_events.json"))
    )

    client = GitHubClient(token="fake")
    agent = GitHubAgent(github_client=client)
    result = await agent.analyze("testuser")

    assert result["username"] == "testuser"
    assert result["user_info"]["name"] == "Test User"
    assert "Python" in result["languages"]
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["metrics"]["repo_influence"] > 0
    assert len(result["top_repos"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_github_agent_user_not_found():
    respx.get("https://api.github.com/users/nonexistent").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    client = GitHubClient(token="fake")
    agent = GitHubAgent(github_client=client)

    with pytest.raises(ValueError, match="not found"):
        await agent.analyze("nonexistent")
```

**Step 2: Run tests**

Run: `pytest tests/test_github_agent_integration.py -v`
Expected: PASS (2 tests)

**Step 3: Commit**

```bash
git add tests/test_github_agent_integration.py
git commit -m "test: add GitHub Agent integration tests"
```

---

### Task 9: Wire GitHub Agent into Analyze Endpoint

**Files:**
- Modify: `src/khire/routers/analyze.py` (refactor to use GitHubAgent)
- Modify: `tests/test_analyze_endpoint.py` (update to match new response)

**Step 1: Rewrite `src/khire/routers/analyze.py`**

```python
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

    # Use LLM to generate human-readable summary
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
```

**Step 2: Update `tests/test_analyze_endpoint.py`**

```python
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from khire.main import app

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@respx.mock
@pytest.mark.asyncio
async def test_analyze_returns_profile():
    respx.get("https://api.github.com/users/testuser").mock(
        return_value=Response(200, json=load_fixture("github_user.json"))
    )
    respx.get("https://api.github.com/users/testuser/repos").mock(
        return_value=Response(200, json=load_fixture("github_repos.json"))
    )
    respx.get("https://api.github.com/users/testuser/events").mock(
        return_value=Response(200, json=load_fixture("github_events.json"))
    )

    with patch("khire.routers.analyze.LLMClient") as MockLLM:
        instance = MockLLM.return_value
        instance.complete = AsyncMock(return_value="Strong ML engineer with open source contributions.")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/analyze/testuser")

    assert resp.status_code == 200
    data = resp.json()
    assert data["github_username"] == "testuser"
    assert "skill_tags" in data
    assert data["overall_score"] > 0
    assert "metrics" in data
    assert len(data["top_repos"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_analyze_user_not_found():
    respx.get("https://api.github.com/users/nobody99999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/analyze/nobody99999")

    assert resp.status_code == 404
```

**Step 3: Run ALL tests**

Run: `pytest -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add src/khire/routers/analyze.py tests/test_analyze_endpoint.py
git commit -m "refactor: wire GitHubAgent into analyze endpoint"
```

---

### Task 10: Benchmark with Known Developers

**Files:**
- Create: `tests/benchmarks/test_scoring_benchmark.py`

This is a validation test — it uses fixture data modeled after well-known developers to verify scoring sanity.

**Step 1: Create the benchmark test**

`tests/benchmarks/__init__.py`: empty

`tests/benchmarks/test_scoring_benchmark.py`:
```python
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
        """A repo with 100k+ stars should score very high."""
        repo = {"stargazers_count": 125000, "forks_count": 25000, "fork": False}
        assert agent._score_repo_influence(repo) >= 0.9

    def test_popular_repo(self, agent):
        """A repo with 1k-10k stars should score moderately high."""
        repo = {"stargazers_count": 5000, "forks_count": 800, "fork": False}
        score = agent._score_repo_influence(repo)
        assert 0.6 <= score <= 0.95

    def test_small_project(self, agent):
        """A repo with <50 stars should score low."""
        repo = {"stargazers_count": 30, "forks_count": 5, "fork": False}
        score = agent._score_repo_influence(repo)
        assert score < 0.5

    def test_new_empty_repo(self, agent):
        """An empty repo with 0 stars."""
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
        """karpathy-like: high repo influence, strong PRs, good collaboration."""
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
        """New developer: small repos, few PRs, limited collaboration."""
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
        """Strong dev should always score higher than junior."""
        strong = {"repo_influence": 0.9, "pr_quality": 0.8, "collaboration": 0.7, "consistency": 0.8, "language_diversity": 0.6}
        junior = {"repo_influence": 0.1, "pr_quality": 0.1, "collaboration": 0.0, "consistency": 0.3, "language_diversity": 0.2}
        assert agent._compute_overall_score(strong) > agent._compute_overall_score(junior)
```

**Step 2: Run benchmark tests**

Run: `pytest tests/benchmarks/ -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/benchmarks/
git commit -m "test: add scoring benchmark tests with developer archetypes"
```

---

## Summary

| Task | What it builds | Tests |
|------|---------------|-------|
| 1 | Project scaffold, config, Docker Compose | — |
| 2 | Health endpoint test | 1 |
| 3 | Developer & SearchQuery models | 2 |
| 4 | LLM abstraction layer (LiteLLM) | 3 |
| 5 | GitHub API client | 4 |
| 6 | `/api/analyze` endpoint | 2 |
| 7 | GitHubAgent contribution scorer | 7 |
| 8 | GitHubAgent integration test | 2 |
| 9 | Wire agent into endpoint | 2 |
| 10 | Scoring benchmarks | 9 |

**Total: 10 tasks, ~32 tests, covering Phase 1 + Phase 2**

After this, Phase 3 (Planner Agent + Smart Search) builds on this foundation by adding intent parsing and multi-agent orchestration.
