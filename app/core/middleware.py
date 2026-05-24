"""Production middleware: security headers, request IDs, rate limiting."""

import logging
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.cors_middleware import apply_cors_headers
from app.core.rate_limit import get_rate_limiter

logger = logging.getLogger(__name__)

AUTH_PATH_MARKERS = ("/auth/login", "/auth/register")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach X-Request-ID for log correlation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Standard security response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        settings = get_settings()
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiting with stricter limits on auth endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled or request.url.path in (
            "/health",
            "/health/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        ):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        is_auth = any(marker in path for marker in AUTH_PATH_MARKERS)
        limit = (
            settings.rate_limit_auth_per_minute
            if is_auth
            else settings.rate_limit_requests_per_minute
        )
        key = f"{client_ip}:auth" if is_auth else f"{client_ip}:api"
        limiter = get_rate_limiter()

        if not limiter.is_allowed(key, limit=limit, window_seconds=60):
            logger.warning("Rate limit exceeded for %s on %s", client_ip, path)
            rate_response = Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )
            return apply_cors_headers(request, rate_response)

        response = await call_next(request)
        remaining = limiter.remaining(key, limit=limit, window_seconds=60)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
