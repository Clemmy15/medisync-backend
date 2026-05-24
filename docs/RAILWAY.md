# Deploying MedisyncAI Backend on Railway

If the service **crashes on startup**, common errors:

```text
ConfigurationError: SECRET_KEY must be at least 32 characters in production
ConfigurationError: ADMIN_PASSWORD must be changed from default in production
```

Railway runs with `DEBUG=false`, so placeholder secrets are rejected. Set **both** `SECRET_KEY` and `ADMIN_PASSWORD` in Variables (see below).

## Required Railway variables

Open your **medisync-backend** service → **Variables** and set:

| Variable | Example / notes |
|----------|-----------------|
| `SECRET_KEY` | **64-character hex** from `openssl rand -hex 32` (required, min 32 chars) |
| `DATABASE_URL` | From Railway PostgreSQL (`postgresql+asyncpg://...`) |
| `DEBUG` | `false` |
| `CORS_ORIGINS` | **Required for browser login.** Set on **Railway** (same place as this API). Comma-separated origins, no trailing slashes. Example: `http://127.0.0.1:5500,https://medisync-ai1.netlify.app` — updating Render CORS does **not** help if the frontend calls the Railway URL. |
| `LLM_PROVIDER` | `mock` (no API key) or `openai` / `gemini` with matching API key |
| `ADMIN_EMAIL` | Your admin login email (e.g. `admin@medisync.ai`) |
| `ADMIN_PASSWORD` | **Required.** Strong password, min 8 chars, letters + numbers. **Cannot** be `admin123!`, `changeme`, or `password` |
| `ENABLE_DOCS` | `true` to expose Swagger; `false` to hide `/docs` (recommended for public production) |
| `CHROMA_PERSIST_DIR` | `/app/data/chroma` (use a Railway volume mounted at `/app/data`) |

### Generate `SECRET_KEY`

**Windows (PowerShell):**

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**macOS / Linux:**

```bash
openssl rand -hex 32
```

Paste the full output into Railway as `SECRET_KEY` (64 hex characters).

## PostgreSQL on Railway

Login and all agents need a working database. Check:

```text
GET https://YOUR-RAILWAY-APP.up.railway.app/health/ready
```

If you see `"database":"disconnected"`, fix `DATABASE_URL` before debugging CORS.

1. Add a **PostgreSQL** plugin to the project.
2. On the **API service** (not only Postgres), set variable `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` or paste the URL from the Postgres service.
3. Ensure the URL uses the **async** driver. If Railway gives `postgresql://`, change the prefix to:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/railway
```

4. Run migrations against that database (Railway shell or one-off deploy command):

```bash
alembic upgrade head
python -m scripts.seed
```

5. Redeploy the API service.

### “CORS blocked” on login with 500 in the console

Often **not** a missing `CORS_ORIGINS` entry. The API returns **500** (e.g. database down) **without** CORS headers, and the browser reports a CORS error. Fix the database first; deploy the latest backend so 500 responses still include CORS headers and a clear JSON `detail`.

## ChromaDB persistence

Mount a volume at `/app/data` and set:

```text
CHROMA_PERSIST_DIR=/app/data/chroma
```

## Startup command (recommended)

In Railway **Settings → Deploy → Start Command** (or use the default Dockerfile `CMD` plus a release phase):

```bash
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

If you use `scripts.seed`, run it once manually or in a one-off job—not on every deploy in production.

## Swagger / API docs (fix 404 on `/docs`)

Docs are at the **root** of your Railway URL, not under `/api/v1`:

| URL | Description |
|-----|-------------|
| `https://YOUR-SERVICE.up.railway.app/docs` | Swagger UI |
| `https://YOUR-SERVICE.up.railway.app/redoc` | ReDoc |
| `https://YOUR-SERVICE.up.railway.app/openapi.json` | OpenAPI schema |

**404 on `/docs`?** Docs are disabled unless `ENABLE_DOCS=true` in Railway Variables. Redeploy after changing it.

Example: if your backend is `https://medisync-backend-production.up.railway.app`, open:

`https://medisync-backend-production.up.railway.app/docs`

API routes themselves stay under `/api/v1` (e.g. `/api/v1/health`, `/api/v1/auth/login`).

---

## After updating variables

1. Save variables in Railway.
2. **Redeploy** the service (Deployments → Redeploy).
3. Check **Deploy Logs** for `Application startup complete`.

## Other startup errors

| Error | Fix |
|-------|-----|
| `ADMIN_PASSWORD must be changed` | Set `ADMIN_PASSWORD` to a strong unique value |
| `OPENAI_API_KEY is required` | Set key or use `LLM_PROVIDER=mock` |
| Database connection failed | Fix `DATABASE_URL` and run `alembic upgrade head` |

See also [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md).
