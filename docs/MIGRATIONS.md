# Database migrations & seed

## `alembic upgrade head` fails on `ix_recommendations_category`

Migration **005** already creates `ix_recommendations_category`. Migration **008** tried to create it again.

**Fix (already in repo):** 008 skips that index and uses `if_not_exists=True` on other indexes.

From `backend/` with `.env` pointing at your Postgres URL:

```powershell
alembic upgrade head
```

If 008 failed halfway and Alembic is still at revision `007`, re-run `alembic upgrade head` after pulling the fix.

If indexes exist but Alembic is stuck, stamp past 008 then continue:

```powershell
alembic stamp 008
alembic upgrade head
```

## `python -m scripts.seed` — ModuleNotFoundError: chromadb

ChromaDB is optional for seeding. The seed script now writes memories to **PostgreSQL only** if `chromadb` is not installed.

Run without installing Chroma on Windows:

```powershell
python -m scripts.seed
```

You only need Chroma for semantic memory search in the running API. On Railway, use a volume for `CHROMA_PERSIST_DIR` or skip Chroma (list/search APIs still work from Postgres).

### Installing Chroma on Windows (optional)

Requires **Microsoft C++ Build Tools** because `chroma-hnswlib` compiles native code:

https://visualstudio.microsoft.com/visual-cpp-build-tools/

Then:

```powershell
pip install -r requirements.txt
```

## Railway checklist

1. `DATABASE_URL` = `postgresql+asyncpg://...` on the **API** service
2. `alembic upgrade head` (Railway shell or CI against that URL)
3. `python -m scripts.seed`
4. Redeploy API

Verify:

```text
GET https://YOUR-APP.up.railway.app/health/ready
→ "database":"connected"
```
