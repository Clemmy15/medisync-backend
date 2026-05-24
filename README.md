# MedisyncAI Backend

Production-ready FastAPI backend for **MedisyncAI** — a Behaviour-Aware Healthcare Recommendation Agent built for the DSN x BluechipTech LLM Agent Challenge.

## Features

- JWT authentication with password hashing
- Adaptive user profiles
- Cross-AI health context import (ChatGPT, Gemini, Claude)
- Dual memory store (PostgreSQL + ChromaDB vectors)
- AI agents: Persona, Recommendation, Review Simulation, Behaviour Analysis, Risk Detection
- Agent reasoning traces for transparency
- Analytics and admin dashboards
- Docker-ready deployment

## Tech Stack

FastAPI · PostgreSQL · SQLAlchemy · Alembic · JWT · ChromaDB · OpenAI/Gemini · Pydantic · Async

## Quick Start (Docker)

```bash
cd backend
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL 16+

### Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Start PostgreSQL, then:

```bash
alembic upgrade head
python -m scripts.seed
uvicorn main:app --reload
```

### Seed Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@medisync.ai | admin123! |
| Demo | demo@medisync.ai | demo12345 |

## Frontend

Static web app in [`../frontend`](../frontend/README.md). Serve with Live Server or `python -m http.server 5500` and ensure `CORS_ORIGINS` includes your frontend URL.

## LLM Configuration

Set `LLM_PROVIDER` in `.env`:

| Value | Description |
|-------|-------------|
| `mock` | Deterministic responses (default, no API key) |
| `openai` | Requires `OPENAI_API_KEY` |
| `gemini` | Requires `GEMINI_API_KEY` |

## Behavioural Memory Engine

Dual-store long-term memory (PostgreSQL + ChromaDB) with semantic search and summarization.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/memory` | Create memory |
| `GET /api/v1/memory` | Retrieve memories |
| `POST /api/v1/memory/search` | Semantic search |
| `PUT /api/v1/memory/{id}` | Update memory |
| `DELETE /api/v1/memory/{id}` | Delete memory |

Details: [docs/MEMORY_ENGINE.md](docs/MEMORY_ENGINE.md)

## Review Simulation Agent (Task A)

Simulates persona-based ratings, reviews, and behavioural reasoning for healthcare apps, wellness products, telemedicine, pharmacies, and fitness programs.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/simulation/review` | Run simulation |
| `GET /api/v1/simulation/history` | Stored simulations |
| `GET /api/v1/simulation/current` | Latest simulation |

Details: [docs/REVIEW_SIMULATION_AGENT.md](docs/REVIEW_SIMULATION_AGENT.md)

## Risk Detection Agent

Detects dangerous symptom patterns, behavioural deterioration, and recurring health concerns. Levels: **low**, **moderate**, **high**.

Details: [docs/RISK_DETECTION_AGENT.md](docs/RISK_DETECTION_AGENT.md)

## Analytics Module

Chart-ready dashboards for active users, imports, recommendations, reviews, personas, and memory growth. Admin only.

Details: [docs/ANALYTICS_MODULE.md](docs/ANALYTICS_MODULE.md)

## Architecture

Clean-architecture layering with dependency injection:

```
backend/app/
├── api/routes/       # Thin HTTP controllers
├── agents/           # AI orchestration (typed AgentResult)
├── services/         # LLM, analytics, reasoning
├── repositories/     # Data access
├── domain/           # Enums & domain types
├── models/           # SQLAlchemy ORM
├── schemas/          # Pydantic request/response
├── core/             # Config, deps, security, logging, exceptions
└── memory/           # ChromaDB vector store
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full system architecture.

**Production readiness**

- [Security Report](docs/SECURITY_REPORT.md)
- [Performance Report](docs/PERFORMANCE_REPORT.md)
- [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)
- [Architecture Audit](docs/AUDIT_REPORT.md) (initial refactor)

## Project Structure

```
backend/
├── app/
│   ├── api/              # Route handlers + helpers
│   ├── agents/           # AI agent implementations
│   ├── domain/           # Shared enums
│   ├── repositories/     # Database access layer
│   ├── memory/           # ChromaDB vector store
│   ├── context_import/   # Context extraction
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # LLM, analytics, reasoning
│   ├── database/         # DB session & base
│   ├── core/             # Config, security, deps, logging
│   └── utils/            # Prompts, helpers
├── alembic/              # Migrations
├── tests/
├── scripts/seed.py
├── main.py
└── docker-compose.yml
```

## Key Endpoints

```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/profile
GET  /api/v1/context-import/prompts       # ChatGPT, Gemini, Claude
GET  /api/v1/context-import/prompt/{platform}
POST /api/v1/context-import/analyze       # structured JSON + confidence
POST /api/v1/context-import/save          # PostgreSQL + ChromaDB
GET  /api/v1/context-import/history
POST /api/v1/recommendations/generate
GET  /api/v1/recommendations/current
GET  /api/v1/recommendations/history
POST /api/v1/simulation/review      # Hackathon Task A
GET  /api/v1/simulation/history
GET  /api/v1/simulation/current
POST /api/v1/persona/generate
GET  /api/v1/persona/current
GET  /api/v1/persona/history
POST /api/v1/analysis/behaviour
POST /api/v1/analysis/risk
GET  /api/v1/analysis/risk/current
GET  /api/v1/analysis/risk/history
GET  /api/v1/analytics/overview        # admin — KPIs + charts
GET  /api/v1/analytics/personas        # admin — persona distribution
GET  /api/v1/analytics/recommendations # admin — recommendation stats
```

All agent endpoints return top-level **`steps`** (and `reasoning_trace`) with transparent reasoning.  
Persisted traces: `GET /api/v1/reasoning/traces`. See [docs/REASONING_TRACES.md](docs/REASONING_TRACES.md).

## Running Tests

```bash
pytest -v
```

## API Documentation

See [docs/API.md](docs/API.md) or open `/docs` for interactive Swagger UI.

## License

Hackathon project — MedisyncAI © 2026
