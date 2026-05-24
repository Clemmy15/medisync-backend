import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes import health as health_routes
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import (
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(level=settings.log_level, debug=settings.debug)
    try:
        settings.validate_runtime()
    except Exception as exc:
        if settings.debug:
            logger.warning("Runtime validation skipped in debug mode: %s", exc)
        else:
            raise
    app.state.settings = settings
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = "/docs" if settings.enable_docs and settings.debug else None
    redoc_url = "/redoc" if settings.enable_docs and settings.debug else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Behaviour-Aware Healthcare Recommendation Agent for the "
            "DSN x BluechipTech LLM Agent Challenge."
        ),
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
    )

    register_exception_handlers(app)
    app.include_router(health_routes.router)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
