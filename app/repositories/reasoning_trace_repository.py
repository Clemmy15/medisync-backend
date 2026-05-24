from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reasoning_trace import ReasoningTrace


class ReasoningTraceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, trace_id: int, user_id: int) -> ReasoningTrace | None:
        result = await self._db.execute(
            select(ReasoningTrace).where(
                ReasoningTrace.id == trace_id,
                ReasoningTrace.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest(
        self,
        user_id: int,
        trace_type: str | None = None,
    ) -> ReasoningTrace | None:
        query = (
            select(ReasoningTrace)
            .where(ReasoningTrace.user_id == user_id)
            .order_by(ReasoningTrace.created_at.desc())
            .limit(1)
        )
        if trace_type is not None:
            query = query.where(ReasoningTrace.trace_type == trace_type)
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        trace_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReasoningTrace]:
        query = (
            select(ReasoningTrace)
            .where(ReasoningTrace.user_id == user_id)
            .order_by(ReasoningTrace.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if trace_type is not None:
            query = query.where(ReasoningTrace.trace_type == trace_type)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: int,
        *,
        trace_type: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(ReasoningTrace).where(
            ReasoningTrace.user_id == user_id
        )
        if trace_type is not None:
            query = query.where(ReasoningTrace.trace_type == trace_type)
        result = await self._db.execute(query)
        return int(result.scalar_one())
