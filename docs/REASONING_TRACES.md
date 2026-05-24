# Transparent Reasoning Traces

Every MedisyncAI **agent response** includes an ordered list of reasoning **steps** so clients can show how a conclusion was reached.

## Response shape

All agent endpoints return top-level `steps` (and `reasoning_trace.steps` for backward compatibility):

```json
{
  "persona_name": "Sleep-Deprived Student",
  "reasoning": "...",
  "confidence_score": 0.87,
  "steps": [
    "Retrieved user profile",
    "Retrieved behavioural memory",
    "Retrieved imported AI context",
    "Analyzed behavioural patterns",
    "Generated persona classification"
  ],
  "reasoning_trace": {
    "steps": [
      "Retrieved user profile",
      "Retrieved behavioural memory",
      "Retrieved imported AI context",
      "Analyzed behavioural patterns",
      "Generated persona classification"
    ]
  }
}
```

## Agents with reasoning traces

| Agent | Endpoint | `trace_type` stored |
|-------|----------|---------------------|
| Persona | `POST /persona/generate` | `persona` |
| Recommendation | `POST /recommendations/generate` | `recommendation` |
| Review simulation | `POST /simulation/review` | `review_simulation` |
| Behaviour analysis | `POST /analysis/behaviour` | `behaviour_analysis` |
| Risk detection | `POST /analysis/risk` | `risk_detection` (linked to `risk_assessments.id`) |
| Memory search | `POST /memory/search` | `memory_search` |
| Memory summarize | `POST /memory/summarize` | `memory_summarize` |
| Context analyze | `POST /context-import/analyze` | `context_analyze` |
| Context save | `POST /context-import/save` | `context_save` |

Traces are persisted in the `reasoning_traces` table (PostgreSQL).

## Query API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reasoning/traces` | List traces (`?trace_type=&limit=&offset=`) |
| GET | `/api/v1/reasoning/traces/latest` | Latest trace (`?trace_type=`) |
| GET | `/api/v1/reasoning/traces/{id}` | Trace by ID |

### Example

```bash
# Generate persona (creates trace)
curl -X POST http://localhost:8000/api/v1/persona/generate \
  -H "Authorization: Bearer $TOKEN"

# List all traces
curl http://localhost:8000/api/v1/reasoning/traces \
  -H "Authorization: Bearer $TOKEN"

# Latest recommendation trace
curl "http://localhost:8000/api/v1/reasoning/traces/latest?trace_type=recommendation" \
  -H "Authorization: Bearer $TOKEN"
```

## Database

Table: `reasoning_traces`

| Column | Description |
|--------|-------------|
| `user_id` | Owner |
| `trace_type` | Agent identifier |
| `reference_id` | Optional link to persona/recommendation/import row |
| `steps` | JSON array of step strings |
| `created_at` | Timestamp |

Created in migration `001_initial_schema`.
