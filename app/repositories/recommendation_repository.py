from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import RecommendationCategory
from app.models.recommendation import Recommendation


class RecommendationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, recommendation: Recommendation) -> Recommendation:
        self._db.add(recommendation)
        await self._db.flush()
        return recommendation

    async def get_by_id(self, rec_id: int, user_id: int) -> Recommendation | None:
        result = await self._db.execute(
            select(Recommendation).where(
                Recommendation.id == rec_id,
                Recommendation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest(
        self,
        user_id: int,
        category: RecommendationCategory | None = None,
    ) -> Recommendation | None:
        query = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
        if category is not None:
            query = query.where(Recommendation.category == category.value)
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        category: RecommendationCategory | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        query = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )
        if category is not None:
            query = query.where(Recommendation.category == category.value)
        result = await self._db.execute(query)
        return list(result.scalars().all())
