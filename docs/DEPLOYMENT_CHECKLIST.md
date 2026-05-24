# Deployment Checklist — MedisyncAI Backend

Use this checklist before staging and production releases.

---

## 1. Environment variables

Copy `.env.example` → `.env` and set:

| Variable | Required | Notes |
|----------|----------|-------|
| `DEBUG` | Yes | **`false`** in production |
| `SECRET_KEY` | Yes | `openssl rand -hex 32` — min 32 chars |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` |
| `CORS_ORIGINS` | Yes | Production frontend URL(s) only |
| `LLM_PROVIDER` | Yes | `openai` or `gemini` |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | If used | Never commit |
| `ADMIN_EMAIL` | Yes | Non-public admin account |
| `ADMIN_PASSWORD` | Yes | Strong unique password |
| `ENABLE_DOCS` | Yes | **`false`** in production |
| `RATE_LIMIT_ENABLED` | Yes | **`true`** |
| `LOG_LEVEL` | Yes | `INFO` or `WARNING` |

---

## 2. Database

```bash
cd backend
alembic upgrade head   # through revision 008
python scripts/seed.py # optional demo data
```

- [ ] PostgreSQL 14+ provisioned
- [ ] Backups enabled (daily minimum)
- [ ] Connection limit ≥ `(workers × DB_POOL_SIZE) + overhead`
- [ ] Migrations applied in CI/CD before traffic shift

---

## 3. Application

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

- [ ] `DEBUG=false` — runtime validation passes on startup
- [ ] OpenAPI `/docs` not publicly accessible
- [ ] Chroma data directory on persistent volume (`CHROMA_PERSIST_DIR`)
- [ ] Process manager (systemd, Docker, K8s) configured with restart policy

---

## 4. Docker (if used)

- [ ] Multi-stage build; non-root user
- [ ] Health check: `GET /health/ready`
- [ ] Secrets via orchestrator secrets, not image layers
- [ ] `chromadb` native deps built in Linux image

---

## 5. Reverse proxy & TLS

- [ ] HTTPS terminated at nginx / ALB / Cloudflare
- [ ] `Strict-Transport-Security` header active (automatic when `DEBUG=false`)
- [ ] Proxy forwards `X-Forwarded-For` if using IP rate limits behind LB
- [ ] WebSocket not required (none used)

---

## 6. Security

- [ ] Default `admin123!` password changed
- [ ] CORS does not include `*`
- [ ] JWT secret rotated from development
- [ ] Admin endpoints tested (403 for non-admin)
- [ ] Rate limits verified on `/auth/login`
- [ ] Review [SECURITY_REPORT.md](SECURITY_REPORT.md)

---

## 7. Observability

- [ ] Logs shipped to aggregator (CloudWatch, Datadog, etc.)
- [ ] `X-Request-ID` included in log format
- [ ] Alerts on `/health/ready` failures
- [ ] Alerts on 5xx rate &gt; threshold
- [ ] LLM provider quota monitoring

---

## 8. Smoke tests (post-deploy)

```bash
curl https://api.example.com/health
curl https://api.example.com/health/ready

# Register + login + protected route
curl -X POST https://api.example.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"Testpass1"}'

curl -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Testpass1"}'
```

- [ ] Health endpoints return 200
- [ ] Auth flow works
- [ ] Agent endpoint returns `steps` in response
- [ ] Admin analytics returns 403 for regular user

---

## 9. Rollback plan

- [ ] Previous container image tagged and retained
- [ ] `alembic downgrade -1` tested in staging if migration risky
- [ ] Database snapshot before major migrations

---

## 10. Post-launch

- [ ] Monitor error rates first 24h
- [ ] Review rate limit 429 volume
- [ ] Confirm backup restore procedure
- [ ] Document on-call runbook
