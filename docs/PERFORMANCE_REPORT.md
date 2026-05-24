# Performance Report — MedisyncAI Backend

**Audit date:** 2026-05-24

---

## Executive summary

The backend is an **async FastAPI** application with **PostgreSQL** (asyncpg) and **ChromaDB** for vector search. Performance is adequate for hackathon/demo scale; this report documents bottlenecks, indexes added, and scaling guidance.

| Component | Rating | Notes |
|-----------|--------|-------|
| API layer | Good | Async I/O throughout |
| PostgreSQL | Good | Indexes added (migration 008) |
| Connection pool | Improved | Configurable pool size |
| ChromaDB | Moderate | Single-node; sync calls in async path |
| LLM calls | Variable | Dominates agent latency |
| Analytics | Good | Aggregations indexed |

---

## Database

### Connection pool (implemented)

```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

`pool_pre_ping=True` avoids stale connections.

**Sizing guide:** `pool_size ≈ (2 × CPU cores) + effective_spindle_count` per worker; multiply by worker count and stay under PostgreSQL `max_connections`.

### Indexes added (migration `008`)

| Table | Index | Use case |
|-------|-------|----------|
| `memories` | `(user_id, created_at)` | List + analytics time series |
| `memories` | `(user_id, category)` | Filtered list |
| `recommendations` | `(user_id, created_at)` | History, analytics |
| `recommendations` | `(category)` | Category analytics |
| `context_imports` | `(user_id, created_at)` | History |
| `personas` | `(user_id, created_at)` | Latest persona |
| `review_simulations` | `(user_id, created_at)` | History |
| `reasoning_traces` | `(user_id, trace_type)` | Filter traces |
| `reasoning_traces` | `(created_at)` | Time-range queries |
| `analytics_events` | `(user_id, created_at)` | Active users |
| `risk_assessments` | `(user_id, created_at)` | Risk history |

Run: `alembic upgrade head`

### Query patterns

| Operation | Complexity | Optimization |
|-----------|------------|--------------|
| User memory list | O(log n) index scan | `(user_id, created_at)` |
| Semantic search | O(n) vector + PG enrich | Chroma top-k limit; cap `limit` ≤ 50 |
| Analytics overview | O(days × tables) | 14-day window; indexed `created_at` |
| Persona generate | 1 LLM + 3–4 DB reads | Cache persona if unchanged |

---

## API latency (typical, mock LLM)

| Endpoint | Expected |
|----------|----------|
| `GET /health` | &lt; 5 ms |
| `GET /health/ready` | &lt; 20 ms |
| `POST /auth/login` | 50–150 ms (bcrypt) |
| `POST /memory` | 20–80 ms (+ Chroma index) |
| `POST /memory/search` | 50–200 ms |
| Agent endpoints | **1–5 s** (real LLM) / &lt; 100 ms (mock) |

---

## ChromaDB

- **PersistentClient** on local disk (`CHROMA_PERSIST_DIR`)
- Embedding + query runs synchronously inside async handlers — acceptable at low QPS
- **Scale-up:** Dedicated Chroma server; async wrapper with `asyncio.to_thread()`
- **Scale-out:** Managed vector DB (Pinecone, pgvector)

---

## LLM provider

Dominant cost and latency. Mitigations:

| Strategy | Impact |
|----------|--------|
| `gpt-4o-mini` / `gemini-1.5-flash` | Lower cost/latency |
| Cache persona/context bundle per user (TTL 5 min) | Fewer tokens |
| Stream responses (future) | Better perceived latency |
| Timeout + circuit breaker | Fail fast on provider outages |

---

## Rate limiting & overload

- Rate limiter prevents auth brute-force and casual API abuse
- Returns **429** with `Retry-After`
- For DDoS, use **CDN/WAF** in front of API

---

## Caching opportunities (future)

| Data | TTL | Invalidation |
|------|-----|--------------|
| User profile + memory context | 5 min | On memory write |
| Latest persona | 10 min | On persona generate |
| Analytics overview | 1 min | Admin dashboard |

---

## Horizontal scaling

```
                    ┌─────────────┐
   Clients ────────►│   Nginx     │ TLS
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Uvicorn-1    Uvicorn-2    Uvicorn-3
              │            │            │
              └────────────┼────────────┘
                           ▼
                    PostgreSQL (RDS)
                           │
                    Chroma / Redis
```

Requirements for multi-worker:

1. Shared PostgreSQL (not SQLite)
2. **Redis** for rate limits and optional sessions
3. Shared Chroma volume or remote vector service
4. Sticky sessions **not** required (stateless JWT)

---

## Monitoring recommendations

| Metric | Tool |
|--------|------|
| Request latency p95 | Prometheus + Grafana |
| DB pool usage | SQLAlchemy pool events |
| 429 rate | Access logs |
| LLM errors | Application logs |
| Readiness failures | K8s probes on `/health/ready` |

---

## Load test targets (suggested)

| Scenario | Target |
|----------|--------|
| Health | 1000 RPS, p95 &lt; 10 ms |
| Authenticated CRUD | 100 RPS, p95 &lt; 200 ms |
| Agent generate | 10 concurrent, p95 &lt; 8 s (real LLM) |
