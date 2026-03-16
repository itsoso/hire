# KHire Architecture

## System Overview

```
                         +-----------------------+
                         |   React Frontend      |
                         |   (Next.js + Tailwind)|
                         |                       |
                         |  /          Search    |
                         |  /analyze   Analyze   |
                         |  /developer Profile   |
                         +----------+------------+
                                    |
                              fetch (REST)
                                    |
+-----------------------------------v------------------------------------+
|                        FastAPI Backend                                  |
|                                                                        |
|  +------------------+  +------------------+  +-------------------+     |
|  | /api/search      |  | /api/analyze/:u  |  | /api/developer/:u |    |
|  | (search.py)      |  | (analyze.py)     |  | /network /scholar |    |
|  +--------+---------+  +--------+---------+  +--------+----------+    |
|           |                      |                     |               |
|  +--------v----------------------v---------------------v----------+   |
|  |                       Agent Layer                              |   |
|  |                                                                |   |
|  |  PlannerAgent          GitHubAgent        ScholarAgent         |   |
|  |  - parse_intent()      - analyze()        - analyze()          |   |
|  |  - search()            - _score_repo()    - co-authors         |   |
|  |  - orchestrate         - _classify_pr()                        |   |
|  |                        - _compute_score() NetworkAgent          |   |
|  |                                           - build_network()    |   |
|  +----------+---------------------+--------------------+----------+   |
|             |                     |                    |               |
|  +----------v----------+ +-------v--------+ +---------v---------+    |
|  |   GitHubClient      | | ScholarClient  | |    LLMClient      |    |
|  |   - get_user()      | | - search_author| |    - complete()   |    |
|  |   - get_repos()     | | - get_papers() | |    - complete_json|    |
|  |   - get_events()    | +-------+--------+ +---------+---------+    |
|  |   - search_users()  |         |                    |               |
|  +----------+----------+         |                    |               |
+-------------|--------------------|--------------------|---------------+
              |                    |                    |
              v                    v                    v
        GitHub API         Semantic Scholar     LLM (Claude/GPT/
        (REST v3)          (Graph API)          DeepSeek via LiteLLM)
```

## Directory Structure

```
KHire/
├── src/khire/
│   ├── main.py                 # FastAPI app + CORS + router registration
│   ├── config.py               # Pydantic Settings (env-based config)
│   ├── database.py             # SQLAlchemy async engine + session
│   ├── models.py               # Developer, SearchQuery (ORM)
│   ├── llm.py                  # LLMClient (LiteLLM multi-model)
│   ├── clients/
│   │   ├── github.py           # GitHubClient (REST API)
│   │   └── scholar.py          # ScholarClient (Semantic Scholar)
│   ├── agents/
│   │   ├── base.py             # AgentMessage dataclass
│   │   ├── github_agent.py     # Contribution scoring engine
│   │   ├── planner_agent.py    # Search orchestrator (ReAct-like)
│   │   ├── scholar_agent.py    # Academic profile analyzer
│   │   └── network_agent.py    # Collaboration graph builder
│   └── routers/
│       ├── analyze.py          # POST /api/analyze/{username}
│       ├── search.py           # POST /api/search
│       └── developer.py        # GET  /api/developer/{username}/*
├── tests/
│   ├── fixtures/               # Mock JSON data (GitHub API responses)
│   ├── benchmarks/             # Scoring accuracy tests
│   ├── test_github_client.py   # 4 tests
│   ├── test_github_agent.py    # 7 tests
│   ├── test_github_agent_integration.py  # 2 tests
│   ├── test_github_search.py   # 2 tests
│   ├── test_scholar_client.py  # 3 tests
│   ├── test_scholar_agent.py   # 3 tests
│   ├── test_planner_agent.py   # 5 tests
│   ├── test_network_agent.py   # 4 tests
│   ├── test_llm.py             # 3 tests
│   ├── test_models.py          # 2 tests
│   ├── test_health.py          # 1 test
│   ├── test_analyze_endpoint.py    # 2 tests
│   ├── test_developer_endpoint.py  # 3 tests
│   ├── test_search_endpoint.py     # 3 tests
│   └── benchmarks/test_scoring_benchmark.py  # 10 tests
├── frontend/
│   └── src/
│       ├── lib/api.ts          # TypeScript API client + interfaces
│       └── app/
│           ├── layout.tsx      # Nav bar (Search | Analyze)
│           ├── page.tsx        # Search page (home)
│           ├── analyze/page.tsx            # Single user analyzer
│           └── developer/[username]/page.tsx  # Profile (tabs)
├── docker-compose.yml          # PostgreSQL 16 + Redis 7
├── pyproject.toml              # Python deps + tool config
└── .env.example                # Environment template
```

## Three-Layer Architecture

### Layer 1: HTTP Routers
Thin controllers that validate input and delegate to agents.

| Endpoint | Method | Router | Agent Used |
|----------|--------|--------|------------|
| `/api/search` | POST | search.py | PlannerAgent |
| `/api/analyze/{username}` | POST | analyze.py | GitHubAgent + LLM |
| `/api/developer/{username}` | GET | developer.py | GitHubAgent + LLM |
| `/api/developer/{username}/network` | GET | developer.py | NetworkAgent |
| `/api/developer/{username}/scholar` | GET | developer.py | ScholarAgent |
| `/health` | GET | main.py | — |

### Layer 2: Agents (Business Logic)

```
PlannerAgent (orchestrator)
│
├── parse_intent(query)     # LLM: natural language → structured intent
│     ↓
├── GitHubClient.search_users()   # Find matching GitHub users
│     ↓
├── GitHubAgent.analyze()   # Score each candidate (parallel)
│     ↓
└── filter + rank           # By skills, stars, overall_score
```

**GitHubAgent Scoring Model:**

| Metric | Weight | How it's computed |
|--------|--------|-------------------|
| repo_influence | 30% | log10(stars + forks*0.5) / 4.5, fork penalty 50% |
| pr_quality | 30% | Classify PRs as trivial/minor/significant/core_feature |
| collaboration | 20% | External PRs / 5, capped at 1.0 |
| consistency | 10% | Event count / 30, capped at 1.0 |
| language_diversity | 10% | Unique languages / 5, capped at 1.0 |

**PR Classification:**
- `core_feature`: >200 lines changed, >5 files
- `significant`: >50 lines changed
- `trivial`: typo/readme/doc patterns, or ≤5 lines in 1 file
- `minor`: everything else

### Layer 3: Clients (External API Wrappers)

| Client | API | Auth | Key Methods |
|--------|-----|------|-------------|
| GitHubClient | api.github.com | Bearer token | get_user, get_repos, get_events, search_users |
| ScholarClient | api.semanticscholar.org | None | search_author, get_author_papers, get_paper |
| LLMClient | Via LiteLLM | API key (env) | complete, complete_json |

## Data Flow: Search Query

```
User: "Find ML engineers who know PyTorch"
  │
  ▼
POST /api/search {query: "..."}
  │
  ▼
PlannerAgent.parse_intent()
  │  LLM → {search_queries: ["ML pytorch language:python"],
  │          required_skills: ["python","pytorch"],
  │          role_type: "ml_engineer"}
  ▼
GitHubClient.search_users("ML pytorch language:python")
  │  → [user_a, user_b, user_c, ...]
  ▼
asyncio.gather(
  GitHubAgent.analyze("user_a"),   # parallel
  GitHubAgent.analyze("user_b"),
  GitHubAgent.analyze("user_c"),
)
  │  → scored profiles with metrics
  ▼
Filter: required_skills ∩ candidate_languages ≠ ∅
Filter: max(repo.stars) >= min_stars
  │
  ▼
Sort by overall_score DESC
  │
  ▼
Response: {candidates: [...], total_found: N, intent: {...}}
```

## Data Model

```
Developer
├── id: UUID (PK)
├── github_username: str (unique, indexed)
├── github_data: JSONB     # repos, contributions, languages
├── scholar_data: JSONB    # papers, citations, co-authors
├── social_data: JSONB     # twitter, blog
├── profile_summary: text  # LLM-generated
├── skill_tags: JSONB      # ["python", "pytorch", ...]
├── overall_score: float   # 0.0 - 1.0
├── network: JSONB         # [{developer_id, relationship, strength}]
├── created_at: timestamp
└── updated_at: timestamp

SearchQuery
├── id: UUID (PK)
├── query_text: text
├── parsed_intent: JSONB
├── results: JSONB         # [developer_id, ...]
├── employer_id: str (nullable)
└── created_at: timestamp
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| HTTP client | httpx (async) |
| LLM integration | LiteLLM (Claude / GPT / DeepSeek) |
| Frontend framework | Next.js 14 (App Router) |
| Styling | TailwindCSS |
| Language | Python 3.12+ / TypeScript |
| Testing | pytest (54 tests) |
| Containers | Docker Compose |

## Frontend Pages

| Route | Page | Data Source |
|-------|------|-------------|
| `/` | Search | POST /api/search |
| `/analyze` | Single user analyzer | POST /api/analyze/{u} |
| `/developer/[username]` | Profile (3 tabs) | GET /api/developer/{u}, /network, /scholar |

**Developer Profile Tabs:**
1. **Overview** — Metrics bars, languages, top repos
2. **Network** — Collaboration connections with strength scores
3. **Academic** — h-index, citations, papers, co-authors
