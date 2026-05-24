"""Ensure CORS headers on every response (including 500 errors)."""

import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def apply_cors_headers(request: Request, response: Response) -> Response:
    """Mirror allowed Origin on responses so browsers can read error bodies."""
    origin = request.headers.get("origin")
    if not origin:
        return response
    settings = get_settings()
    if origin not in settings.cors_origin_list:
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers.setdefault("Vary", "Origin")
    return response


class CorsOnErrorMiddleware(BaseHTTPMiddleware):
    """
    Outermost safety net: attach CORS headers even when inner middleware or
    handlers return 500 without passing through CORSMiddleware correctly.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception before response (method=%s path=%s)",
                request.method,
                request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "An unexpected error occurred"},
            )
        return apply_cors_headers(request, response)
