# Security Report — MedisyncAI Backend

**Audit date:** 2026-05-24  
**Scope:** Authentication, authorization, API security, validation, rate limiting, logging, error handling

---

## Executive summary

The backend was audited for production deployment. Several controls were already in place (JWT auth, bcrypt passwords, admin-gated analytics). This audit **implemented additional hardening** and documents residual risks.

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ✅ Strong | JWT (HS256), bcrypt, `iat`/`exp` claims |
| Authorization | ✅ Strong | User-scoped data; admin routes require `is_admin` |
| API security | ✅ Improved | Security headers, CORS lockdown, docs disabled in prod |
| Validation | ✅ Improved | Pydantic on all inputs; password strength rules |
| Rate limiting | ✅ Added | Per-IP sliding window; stricter on `/auth/*` |
| Logging | ✅ Adequate | Structured stdout; request IDs for correlation |
| Error handling | ✅ Improved | No stack traces to clients; typed domain errors |
| Secrets | ⚠️ Config | Runtime validation blocks default secrets in prod |

---

## Authentication

### Implemented

- **Password hashing:** bcrypt via `get_password_hash()` / `verify_password()`
- **JWT access tokens:** `sub` (user id), `iat`, `exp`, `type=access`
- **Token expiry:** Configurable `ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h)
- **Login:** Generic error message ("Invalid email or password") to prevent user enumeration
- **Registration:** Email uniqueness enforced; password min 8 chars + letter + digit

### Recommendations

| Priority | Item |
|----------|------|
| Medium | Add refresh tokens or shorter access token TTL (15–60 min) for production |
| Medium | Implement token revocation blocklist on logout/password change |
| Low | Add MFA for admin accounts |

---

## Authorization

### Implemented

- `get_current_user` — Bearer JWT required on protected routes
- `get_current_admin` — Returns 403 if `is_admin` is false
- **Analytics** (`/api/v1/analytics/*`) — Admin only
- **Admin** (`/api/v1/admin/*`) — Admin only
- Repositories scope queries by `user_id` for user-owned resources

### Verified public endpoints (intentional)

| Endpoint | Rationale |
|----------|-----------|
| `POST /auth/register`, `POST /auth/login` | Public auth |
| `GET /context-import/prompts` | Static copy-paste prompts (no PII) |
| `GET /health`, `GET /health/ready` | Load balancer probes |

### Residual risks

| Risk | Mitigation |
|------|------------|
| IDOR if repository forgets `user_id` filter | Code review + integration tests per resource |
| Admin can list all users/memories | By design; restrict admin accounts in production |

---

## API security

### Implemented (this audit)

| Control | Implementation |
|---------|----------------|
| Security headers | `SecurityHeadersMiddleware` — `X-Content-Type-Options`, `X-Frame-Options`, `HSTS` (non-debug) |
| Request correlation | `X-Request-ID` on every response |
| CORS | Explicit origin list; wildcard blocked in production validation |
| OpenAPI UI | Disabled when `DEBUG=false` (`ENABLE_DOCS=false`) |
| Rate limiting | `RateLimitMiddleware` — 120 req/min API, 10 req/min auth |
| Pagination caps | Admin list endpoints max 200 items |

### CORS configuration

```env
CORS_ORIGINS=https://app.yourdomain.com
```

Never use `*` with `allow_credentials=True`.

---

## Validation

- All request bodies use **Pydantic v2** models with `Field` constraints
- Email fields use `EmailStr`
- Memory/content fields have max length (e.g. 10,000 chars)
- Enums for categories, risk levels, platforms
- `RequestValidationError` returns consistent 422 JSON

---

## Rate limiting

| Scope | Default limit |
|-------|----------------|
| General API | 120 requests / minute / IP |
| Auth (`/auth/login`, `/auth/register`) | 10 requests / minute / IP |

**Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` (429)

**Production note:** In-memory limiter is per-process. Use **Redis-backed** rate limiting behind a load balancer with multiple workers.

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_AUTH_PER_MINUTE=10
```

---

## Logging

- Format: `timestamp | level | logger | message`
- Uvicorn access logs throttled to WARNING
- LLM and application errors logged with `exc_info` server-side only
- Attach `X-Request-ID` in log aggregation (log from middleware/request state in future enhancement)

---

## Error handling

| Exception | HTTP | Client body |
|-----------|------|-------------|
| `NotFoundError` | 404 | `detail` + `errors` |
| `ConflictError` | 409 | `detail` + `errors` |
| `AuthenticationError` | 401 | `detail` |
| `AuthorizationError` | 403 | `detail` |
| `LLMServiceError` | 503 | `detail` (no provider internals) |
| Unhandled | 500 | Generic message only |

---

## Secrets & configuration

Production startup (`DEBUG=false`) **fails fast** if:

- `SECRET_KEY` is default placeholder or &lt; 32 characters
- `CORS_ORIGINS` contains `*`
- `ADMIN_PASSWORD` is a known default
- LLM API keys missing for selected provider

Generate secret:

```bash
openssl rand -hex 32
```

---

## Dependency security

- Pin versions in `requirements.txt`
- Run `pip audit` or Dependabot in CI
- ChromaDB pulls native deps — build in Docker for reproducibility

---

## Checklist before go-live

- [ ] Rotate `SECRET_KEY`, `ADMIN_PASSWORD`, database credentials
- [ ] Set `DEBUG=false`, `ENABLE_DOCS=false`
- [ ] Restrict `CORS_ORIGINS` to production frontend URL(s)
- [ ] TLS termination at reverse proxy (nginx / ALB)
- [ ] Redis rate limiter if running &gt;1 worker
- [ ] Disable default admin in seed or use strong random password
