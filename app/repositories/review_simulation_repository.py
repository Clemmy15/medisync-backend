from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import SimulationTargetType
from app.models.review_simulation import ReviewSimulation


class ReviewSimulationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, simulation: ReviewSimulation) -> ReviewSimulation:
        self._db.add(simulation)
        await self._db.flush()
        return simulation

    async def get_latest(
        self,
        user_id: int,
        target_type: SimulationTargetType | None = None,
    ) -> ReviewSimulation | None:
        query = (
            select(ReviewSimulation)
            .where(ReviewSimulation.user_id == user_id)
            .order_by(ReviewSimulation.created_at.desc())
            .limit(1)
        )
        if target_type is not None:
            query = query.where(ReviewSimulation.target_type == target_type.value)
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        target_type: SimulationTargetType | None = None,
        limit: int = 50,
    ) -> list[ReviewSimulation]:
        query = (
            select(ReviewSimulation)
            .where(ReviewSimulation.user_id == user_id)
            .order_by(ReviewSimulation.created_at.desc())
            .limit(limit)
        )
        if target_type is not None:
            query = query.where(ReviewSimulation.target_type == target_type.value)
        result = await self._db.execute(query)
        return list(result.scalars().all())
