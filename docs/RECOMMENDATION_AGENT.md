# Recommendation Agent

Generates personalized healthcare recommendations by reasoning over:

1. **User profile** — demographics, goals, sleep, stress, diet
2. **Persona** — latest behavioural persona classification
3. **Behavioural memory** — long-term PostgreSQL + ChromaDB memories
4. **Imported context** — cross-AI health context imports

## Recommendation Categories

| Category | Description |
|----------|-------------|
| `health_apps` | Mobile/digital health tracking tools |
| `wellness_plans` | Holistic diet, activity, mindfulness plans |
| `productivity_wellness` | Work-life balance and ergonomic health |
| `sleep_improvement` | Sleep hygiene and scheduling |
| `hydration_improvement` | Hydration habits and goals |
| `stress_reduction` | Stress management and coping strategies |

## Reasoning Flow

The agent **must reason before recommending**. Each generation stores a reasoning trace:

1. Retrieved user profile  
2. Retrieved user persona  
3. Retrieved behavioural memory  
4. Retrieved imported AI context  
5. Analyzed user context  
6. Focused recommendation category  
7. Reasoned about user needs before recommending  
8. Generated personalized recommendation  

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/recommendations/generate` | Generate recommendation |
| GET | `/api/v1/recommendations/current` | Latest recommendation |
| GET | `/api/v1/recommendations/history` | History (`?category=`) |

## Request / Response

**POST /generate**

```json
{
  "category": "sleep_improvement"
}
```

`category` is optional; the agent selects the best fit if omitted.

**Response**

```json
{
  "category": "sleep_improvement",
  "recommendation": "Use a consistent 10:30 PM wind-down...",
  "reasoning": "Your profile shows 5-6h sleep...",
  "confidence": 0.88,
  "reasoning_trace": {
    "steps": ["Retrieved user profile", "..."]
  }
}
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "sleep_improvement"}'
```

## Migration

```bash
alembic upgrade head  # revision 005 adds category + sources_used
```
