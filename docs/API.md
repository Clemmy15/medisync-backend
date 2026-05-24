# MedisyncAI API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Current user (protected) |

## Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/profile` | Create profile |
| GET | `/profile` | Get profile |
| PUT | `/profile` | Update profile |

## Context Import (Cross-AI Health Context)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/context-import/prompts` | None | Prompts for ChatGPT, Gemini, and Claude |
| GET | `/context-import/prompt/{platform}` | None | Prompt for one platform |
| GET | `/context-import/prompt?platform=chatgpt` | None | Prompt with query param |
| POST | `/context-import/analyze` | User | Extract structured JSON + confidence |
| POST | `/context-import/save` | User | Persist to PostgreSQL + ChromaDB |
| GET | `/context-import/history` | User | Import history for current user |

**Analyze response shape:**
```json
{
  "symptoms": [],
  "habits": [],
  "sleep_patterns": [],
  "hydration_behaviour": [],
  "stress_indicators": [],
  "communication_preferences": [],
  "health_goals": [],
  "goals": [],
  "confidence": 0.92,
  "field_confidence": { "symptoms": 0.88, "...": 0.0 },
  "summary": "..."
}
```

## Behavioural Memory Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memory` | Create memory (PostgreSQL + ChromaDB) |
| GET | `/memory` | List memories (`?category=health`) |
| GET | `/memory/{id}` | Get single memory |
| PUT | `/memory/{id}` | Update memory |
| POST | `/memory/search` | Semantic vector search |
| POST | `/memory/summarize` | Summarize memories by category |
| DELETE | `/memory/{id}` | Delete memory |

Memory types: `health`, `behaviour`, `recommendation`, `communication`.  
See [MEMORY_ENGINE.md](MEMORY_ENGINE.md) for full documentation.

## Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/persona/generate` | Generate persona (profile + memory + imports) |
| GET | `/persona/current` | Latest persona |
| GET | `/persona/history` | Persona history |
| POST | `/recommendations/generate` | Generate (profile + persona + memory + imports) |
| GET | `/recommendations/current` | Latest recommendation |
| GET | `/recommendations/history` | History (`?category=sleep_improvement`) |

Categories: `health_apps`, `wellness_plans`, `productivity_wellness`, `sleep_improvement`, `hydration_improvement`, `stress_reduction`.  
See [RECOMMENDATION_AGENT.md](RECOMMENDATION_AGENT.md).
| POST | `/simulation/review` | Review simulation (Task A) |
| GET | `/simulation/history` | Simulation history |
| GET | `/simulation/current` | Latest simulation |

Target types: `healthcare_apps`, `wellness_products`, `telemedicine_services`, `pharmacies`, `fitness_programs`.  
See [REVIEW_SIMULATION_AGENT.md](REVIEW_SIMULATION_AGENT.md).
| POST | `/analysis/behaviour` | Behaviour analysis |
| POST | `/analysis/risk` | Risk detection (symptom patterns, deterioration, recurring concerns) |
| GET | `/analysis/risk/current` | Latest risk assessment |
| GET | `/analysis/risk/history` | Risk assessment history |

Risk levels: `low`, `moderate`, `high`. See [RISK_DETECTION_AGENT.md](RISK_DETECTION_AGENT.md).

All agent POST responses include `"steps": []` (see [REASONING_TRACES.md](REASONING_TRACES.md)).

## Reasoning traces (stored)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reasoning/traces` | List traces (`?trace_type=`) |
| GET | `/reasoning/traces/latest` | Latest trace |
| GET | `/reasoning/traces/{id}` | Trace by ID |

## Analytics & Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics/overview` | Admin | KPIs + 14-day activity & memory charts |
| GET | `/analytics/personas` | Admin | Persona distribution + chart data |
| GET | `/analytics/recommendations` | Admin | Category breakdown + daily chart |

See [ANALYTICS_MODULE.md](ANALYTICS_MODULE.md).
| GET | `/admin/users` | All users (admin) |
| GET | `/admin/analytics` | Admin analytics |
| GET | `/admin/memory` | All memories (admin) |
| GET | `/admin/recommendations` | All recommendations (admin) |
