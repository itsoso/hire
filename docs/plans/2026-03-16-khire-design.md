# KHire: GitHub-Based AI Talent Recruitment Platform

## Overview

KHire is a full-featured AI talent recruitment platform that evaluates developers based on their actual GitHub contributions, academic output, and social influence — rather than traditional resumes. Inspired by Dinq's approach described in the GeekPark article (2026/01/20).

**Core thesis**: In the AI era, outputs (commits, papers, PRs) are more honest than resumes.

## Architecture: Agent Orchestration

```
React Frontend (Search UI, Developer Profiles, Network Graph)
        │ REST / WebSocket
FastAPI Backend
  ├── Planner Agent (intent parsing, task decomposition)
  ├── GitHub Agent (PR quality, contributions, tech stack)
  ├── Scholar Agent (papers, citations, co-authors)
  ├── Social Agent (Twitter, Reddit, blog influence)
  ├── Ranking Agent (scoring, profile synthesis, network graph)
  └── LLM Abstraction Layer (Claude / GPT / DeepSeek)
        │
PostgreSQL + Redis (persistence + caching)
```

### Key Design Decisions

- **Agent architecture** over pipeline: flexibility for complex/fuzzy queries
- **Multi-LLM support**: abstraction layer to switch between Claude, GPT, DeepSeek
- **Python (FastAPI) + React**: Python backend for AI/data processing, React frontend
- **TDD approach**: tests written before implementation at each phase

## Data Model

### Developer (core entity)
- `github_username`: str
- `github_data`: repos, contributions (with quality scores), languages, commit frequency
- `scholar_data`: papers (with venue, citations, author position), h_index, co_authors
- `social_data`: twitter followers, blog posts
- `profile_summary`: str (LLM-generated natural language profile)
- `skill_tags`: [str]
- `overall_score`: float
- `network`: [{developer_id, relationship_type, strength}]

### SearchQuery
- `query_text`: natural language search
- `parsed_intent`: structured intent from Planner
- `results`: [developer_id]
- `employer_id`

### Employer
- company info, saved candidates

## API Design

| Endpoint | Function |
|----------|----------|
| `POST /api/analyze/{github_username}` | Analyze a GitHub user, generate profile |
| `POST /api/search` | Natural language talent search |
| `GET /api/developer/{id}` | Get developer profile |
| `GET /api/developer/{id}/network` | Get relationship network |
| `POST /api/compare` | Compare multiple candidates |
| `WebSocket /ws/search` | Real-time search with streaming agent reasoning |

## Agent Communication

```python
class AgentMessage:
    task_id: str
    agent_type: str  # "planner" | "github" | "scholar" | "social" | "ranking"
    action: str      # "analyze_user" | "search_repos" | "rank_candidates"
    payload: dict
    result: dict | None
    status: str      # "pending" | "running" | "completed" | "failed"
```

## GitHub Agent: Contribution Analysis Dimensions

1. **PR Quality**: core feature vs doc fix, complexity, review feedback
2. **Repository Influence**: stars, forks, dependency count of contributed repos
3. **Technical Depth**: language diversity, framework expertise, contribution consistency
4. **Maintainer Status**: owner/maintainer roles, issue triage activity
5. **Collaboration Signal**: code review participation, cross-project contributions

## Development Cycle

Each phase follows: **Search/Research → Plan → Write Tests → Implement → Verify**

### Phase 1: Infrastructure (Week 1)
- Research: GitHub API limits, auth, available data
- Plan: Project scaffold (FastAPI + React + PostgreSQL + Redis)
- Test: GitHub API client integration tests
- Implement: LLM abstraction layer + GitHub API client + project skeleton
- Verify: Successfully fetch user info from GitHub API

### Phase 2: GitHub Analysis Engine (Week 2-3)
- Research: PR quality evaluation metrics, open-source scoring models
- Plan: GitHub Agent scoring algorithm design
- Test: Scoring accuracy tests using known developers (e.g., karpathy, jxnl)
- Implement: GitHub Agent — PR analysis, contribution scoring, tech stack detection
- Verify: Run scoring on 10 known developers, manual validation

### Phase 3: Planner + Smart Search (Week 3-4)
- Research: ReAct architecture best practices, agent orchestration frameworks
- Plan: Planner Agent intent parsing and task decomposition
- Test: End-to-end tests with 10 typical search scenarios
- Implement: Planner Agent + search API + candidate ranking
- Verify: Reproduce article scenarios (e.g., "find Sora2 core Chinese contributors")

### Phase 4: Network Graph + Profiles (Week 4-5)
- Research: Co-author relationship extraction, graph database options
- Plan: Network construction algorithm
- Test: Relationship graph accuracy tests
- Implement: Scholar Agent + network graph + profile generation
- Verify: Validate graph completeness and accuracy

### Phase 5: Frontend + Employer Dashboard (Week 5-6)
- Research: Dinq/LinkedIn interaction patterns
- Plan: Frontend pages and interaction flows
- Test: Component tests + E2E tests
- Implement: React frontend — search UI, developer profiles, network visualization
- Verify: End-to-end walkthrough, UX evaluation

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Celery (async tasks)
- **Frontend**: React 18+, Next.js, TailwindCSS, D3.js (network graph)
- **Database**: PostgreSQL (primary), Redis (cache/sessions)
- **AI**: LiteLLM (multi-model abstraction), LangChain/LangGraph (agent orchestration)
- **External APIs**: GitHub REST/GraphQL API, Google Scholar (scraping), Twitter API
- **Testing**: pytest, pytest-asyncio, React Testing Library, Playwright (E2E)
