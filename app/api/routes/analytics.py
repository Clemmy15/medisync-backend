from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_analytics_service, get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    PersonaAnalyticsResponse,
    RecommendationAnalytics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="Platform analytics overview (admin)",
    description=(
        "Aggregated metrics: active users, imported contexts, recommendations, "
        "reviews simulated, personas, and memory growth. Includes chart-ready "
        "14-day activity and memory growth series."
    ),
)
async def analytics_overview(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> AnalyticsOverview:
    return await analytics.get_overview(db)


@router.get(
    "/personas",
    response_model=PersonaAnalyticsResponse,
    summary="Persona distribution analytics (admin)",
    description="Persona counts, percentages, and doughnut/bar chart data.",
)
async def analytics_personas(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> PersonaAnalyticsResponse:
    return await analytics.get_persona_distribution(db)


@router.get(
    "/recommendations",
    response_model=RecommendationAnalytics,
    summary="Recommendation analytics (admin)",
    description=(
        "Recommendation totals, confidence, category breakdown, and daily "
        "chart series for dashboards."
    ),
)
async def analytics_recommendations(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> RecommendationAnalytics:
    return await analytics.get_recommendation_analytics(db)
