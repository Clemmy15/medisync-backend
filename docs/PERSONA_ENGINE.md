# User Persona Engine

Generates behavioural healthcare personas by combining:

1. **Profile data** — age, occupation, stress, sleep, goals, communication style
2. **Behavioural memory** — PostgreSQL + ChromaDB long-term memories
3. **Imported AI context** — ChatGPT / Gemini / Claude cross-import summaries
4. **Behavioural patterns** — heuristic signals derived from memory content

## Canonical Personas

- Sleep-Deprived Student
- Busy Professional
- Fitness Enthusiast
- Budget-Conscious User
- Busy Parent
- Health-Conscious Senior

Custom personas are generated when no canonical type fits well.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/persona/generate` | Generate and store persona |
| GET | `/api/v1/persona/current` | Latest persona |
| GET | `/api/v1/persona/history` | Persona history (`?limit=20`) |

## Response Format

```json
{
  "persona_name": "Sleep-Deprived Student",
  "reasoning": "Profile shows university student with 5-6h sleep...",
  "confidence_score": 0.87,
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

## Example

```bash
# Ensure profile and memory exist, then:
curl -X POST http://localhost:8000/api/v1/persona/generate \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8000/api/v1/persona/history \
  -H "Authorization: Bearer $TOKEN"
```

## Migration

```bash
alembic upgrade head  # revision 004 adds personas.sources_used
```
