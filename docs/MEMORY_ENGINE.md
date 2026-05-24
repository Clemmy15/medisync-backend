# Behavioural Memory Engine

Long-term user memory with **PostgreSQL** persistence and **ChromaDB** semantic retrieval.

## Memory Types

| Category | Label | Use case |
|----------|-------|----------|
| `health` | Health Memory | Symptoms, vitals, conditions, health goals |
| `behaviour` | Behaviour Memory | Habits, routines, lifestyle patterns |
| `recommendation` | Recommendation Memory | Past recommendations and outcomes |
| `communication` | Communication Memory | Tone, format, and style preferences |

## Architecture

```
POST/GET/PUT/DELETE /memory
         │
         ▼
   MemoryAgent (facade)
         │
         ▼
 BehaviouralMemoryEngine
    ├── MemoryRepository → PostgreSQL
    └── ChromaMemoryStore → vector embeddings
```

Every **create** and **update** syncs both stores. **Delete** removes from both. **Search** uses ChromaDB cosine similarity with PostgreSQL enrichment.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/memory` | Create memory |
| GET | `/api/v1/memory` | List memories (`?category=health&limit=50`) |
| GET | `/api/v1/memory/{id}` | Get one memory |
| PUT | `/api/v1/memory/{id}` | Update content and/or category |
| POST | `/api/v1/memory/search` | Semantic search |
| POST | `/api/v1/memory/summarize` | Summarize memories |
| DELETE | `/api/v1/memory/{id}` | Delete memory |

All endpoints require JWT authentication (except health check).

## Examples

### Create Health Memory

```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "health", "content": "Reports headaches after 6h sleep"}'
```

### Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "sleep and stress patterns", "limit": 5}'
```

Response:

```json
{
  "query": "sleep and stress patterns",
  "total": 2,
  "results": [
    {
      "memory_id": 3,
      "category": "behaviour",
      "content": "Studies late until 2am before exams",
      "relevance_score": 0.87
    }
  ]
}
```

### Summarize

```bash
curl -X POST http://localhost:8000/api/v1/memory/summarize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": null, "max_memories": 50}'
```

## Migration

```bash
alembic upgrade head
```

Adds `memories.updated_at` and category index (revision `003`).

## Testing

```bash
pytest tests/test_memory_engine.py tests/test_memory_engine_unit.py -v
```
