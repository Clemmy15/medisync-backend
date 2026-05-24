import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.engine import AnalyticsEngine
from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics import (
    AnalyticsOverview,
    PersonaAnalyticsResponse,
    RecommendationAnalytics,
)
from app.utils.json_helpers import safe_json_dumps

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self) -> None:
        self._engine = AnalyticsEngine()

    async def track_event(
        self,
        db: AsyncSession,
        event_type: str,
        user_id: int | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> None:
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=safe_json_dumps(event_data) if event_data else None,
        )
        db.add(event)
        logger.debug("Tracked event %s for user %s", event_type, user_id)

    async def get_overview(self, db: AsyncSession) -> AnalyticsOverview:
        return await self._engine.get_overview(db)

    async def get_persona_distribution(
        self, db: AsyncSession
    ) -> PersonaAnalyticsResponse:
        return await self._engine.get_persona_distribution(db)

    async def get_recommendation_analytics(
        self, db: AsyncSession
    ) -> RecommendationAnalytics:
        return await self._engine.get_recommendation_analytics(db)
