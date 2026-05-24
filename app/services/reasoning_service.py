import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reasoning_trace import ReasoningTrace
from app.repositories.reasoning_trace_repository import ReasoningTraceRepository
from app.schemas.reasoning import ReasoningSteps, ReasoningTraceResponse

logger = logging.getLogger(__name__)


class ReasoningService:
    async def save_trace(
        self,
        db: AsyncSession,
        user_id: int,
        trace_type: str,
        steps: list[str],
        reference_id: int | None = None,
    ) -> ReasoningTrace:
        trace = ReasoningTrace(
            user_id=user_id,
            trace_type=trace_type,
            reference_id=reference_id,
            steps=json.dumps(steps),
        )
        db.add(trace)
        await db.flush()
        logger.debug(
            "Saved reasoning trace type=%s user_id=%s ref=%s steps=%d",
            trace_type,
            user_id,
            reference_id,
            len(steps),
        )
        return trace

    async def list_user_traces(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        trace_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReasoningTraceResponse], int]:
        repo = ReasoningTraceRepository(db)
        traces = await repo.list_by_user(
            user_id, trace_type=trace_type, limit=limit, offset=offset
        )
        total = await repo.count_by_user(user_id, trace_type=trace_type)
        return [self.to_response(t) for t in traces], total

    async def get_trace(
        self,
        db: AsyncSession,
        trace_id: int,
        user_id: int,
    ) -> ReasoningTraceResponse | None:
        repo = ReasoningTraceRepository(db)
        trace = await repo.get_by_id(trace_id, user_id)
        return self.to_response(trace) if trace else None

    async def get_latest_trace(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        trace_type: str | None = None,
    ) -> ReasoningTraceResponse | None:
        repo = ReasoningTraceRepository(db)
        trace = await repo.get_latest(user_id, trace_type=trace_type)
        return self.to_response(trace) if trace else None

    @staticmethod
    def build_steps_response(steps: list[str]) -> ReasoningSteps:
        return ReasoningSteps(steps=steps)

    @staticmethod
    def to_response(trace: ReasoningTrace) -> ReasoningTraceResponse:
        steps: list[str] = json.loads(trace.steps)
        return ReasoningTraceResponse(
            id=trace.id,
            trace_type=trace.trace_type,
            reference_id=trace.reference_id,
            steps=steps,
            created_at=trace.created_at,
        )
