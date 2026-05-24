import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.cors_middleware import apply_cors_headers
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    LLMServiceError,
    MedisyncError,
    NotFoundError,
)

logger = logging.getLogger(__name__)


def _cors_json(request: Request, status_code: int, content: dict) -> JSONResponse:
    return apply_cors_headers(request, JSONResponse(status_code=status_code, content=content))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _cors_json(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            jsonable_encoder(
                {"detail": "Validation error", "errors": exc.errors()}
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return _cors_json(
            request,
            status.HTTP_404_NOT_FOUND,
            {"detail": exc.message, "errors": exc.details},
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return _cors_json(
            request,
            status.HTTP_409_CONFLICT,
            {"detail": exc.message, "errors": exc.details},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        response = _cors_json(
            request,
            status.HTTP_401_UNAUTHORIZED,
            {"detail": exc.message},
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(AuthorizationError)
    async def forbidden_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return _cors_json(
            request,
            status.HTTP_403_FORBIDDEN,
            {"detail": exc.message},
        )

    @app.exception_handler(LLMServiceError)
    async def llm_handler(request: Request, exc: LLMServiceError) -> JSONResponse:
        logger.error("LLM service error: %s", exc.message, exc_info=exc)
        return _cors_json(
            request,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            {"detail": exc.message, "errors": exc.details},
        )

    @app.exception_handler(MedisyncError)
    async def medisync_handler(request: Request, exc: MedisyncError) -> JSONResponse:
        logger.error("Application error: %s", exc.message, exc_info=exc)
        return _cors_json(
            request,
            status.HTTP_400_BAD_REQUEST,
            {"detail": exc.message, "errors": exc.details},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        detail = "An unexpected error occurred"
        # Surface DB connectivity issues (common on fresh Railway deploys)
        err_name = type(exc).__name__
        if "OperationalError" in err_name or "Connection" in str(exc):
            detail = (
                "Database unavailable. Set DATABASE_URL on Railway, "
                "run alembic upgrade head, then redeploy."
            )
        return _cors_json(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"detail": detail},
        )
