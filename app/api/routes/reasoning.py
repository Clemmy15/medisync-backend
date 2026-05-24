from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_reasoning_service
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.reasoning import ReasoningTraceListResponse, ReasoningTraceResponse
from app.services.reasoning_service import ReasoningService

router = APIRouter()


@router.get(
    "/traces",
    response_model=ReasoningTraceListResponse,
    summary="List stored reasoning traces for the current user",
    description=(
        "Returns persisted step-by-step reasoning from all agents "
        "(persona, recommendation, review simulation, analysis, memory, context import)."
    ),
)
async def list_reasoning_traces(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[ReasoningService, Depends(get_reasoning_service)],
    trace_type: str | None = Query(
        default=None,
        description=(
            "Filter: persona | recommendation | review_simulation | "
            "behaviour_analysis | risk_detection | memory_search | memory_summarize | "
            "context_analyze | context_save"
        ),
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ReasoningTraceListResponse:
    traces, total = await service.list_user_traces(
        db,
        current_user.id,
        trace_type=trace_type,
        limit=limit,
        offset=offset,
    )
    return ReasoningTraceListResponse(traces=traces, total=total)


@router.get(
    "/traces/latest",
    response_model=ReasoningTraceResponse,
    summary="Get the latest reasoning trace",
)
async def get_latest_reasoning_trace(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[ReasoningService, Depends(get_reasoning_service)],
    trace_type: str | None = Query(default=None),
) -> ReasoningTraceResponse:
    trace = await service.get_latest_trace(
        db, current_user.id, trace_type=trace_type
    )
    if not trace:
        raise NotFoundError(
            "No reasoning trace found for this user.",
            details={"trace_type": trace_type},
        )
    return trace


@router.get(
    "/traces/{trace_id}",
    response_model=ReasoningTraceResponse,
    summary="Get a reasoning trace by ID",
)
async def get_reasoning_trace(
    trace_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[ReasoningService, Depends(get_reasoning_service)],
) -> ReasoningTraceResponse:
    trace = await service.get_trace(db, trace_id, current_user.id)
    if not trace:
        raise NotFoundError(
            "Reasoning trace not found",
            details={"trace_id": trace_id},
        )
    return trace
