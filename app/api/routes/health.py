"""Health and readiness probes for orchestrators."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_engine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_liveness() -> dict[str, str]:
    settings = get_settings()
    return {"status": "healthy", "service": settings.app_name}


@router.get("/health/ready")
async def health_readiness() -> JSONResponse:
    """Readiness: verifies database connectivity."""
    settings = get_settings()
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "service": settings.app_name,
                "database": "connected",
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": settings.app_name,
                "database": "disconnected",
                "detail": str(exc) if settings.debug else "Database unavailable",
            },
        )
