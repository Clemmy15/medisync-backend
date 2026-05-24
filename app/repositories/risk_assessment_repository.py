from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, assessment: RiskAssessment) -> RiskAssessment:
        self._db.add(assessment)
        await self._db.flush()
        return assessment

    async def get_latest(self, user_id: int) -> RiskAssessment | None:
        result = await self._db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, *, limit: int = 50) -> list[RiskAssessment]:
        result = await self._db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
