from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_analytics_service, get_current_admin, get_user_repository
from app.database.session import get_db
from app.models.memory import Memory
from app.models.recommendation import Recommendation
from app.models.review_simulation import ReviewSimulation
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import AnalyticsOverview
from app.schemas.auth import UserResponse
from app.schemas.memory import MemoryResponse
from app.schemas.recommendation import RecommendationHistoryItem
from app.schemas.review_simulation import ReviewSimulationHistoryItem
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/users", response_model=list[UserResponse], summary="List all users (admin)")
async def list_users(
    _: Annotated[User, Depends(get_current_admin)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[User]:
    return await users.list_all(limit=limit, offset=offset)


@router.get("/analytics", response_model=AnalyticsOverview, summary="Admin analytics")
async def admin_analytics(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> AnalyticsOverview:
    return await analytics.get_overview(db)


@router.get("/memory", response_model=list[MemoryResponse], summary="List all memories (admin)")
async def admin_memories(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MemoryResponse]:
    result = await db.execute(
        select(Memory).order_by(Memory.created_at.desc()).limit(limit)
    )
    return [MemoryResponse.model_validate(m) for m in result.scalars().all()]


@router.get(
    "/recommendations",
    response_model=list[RecommendationHistoryItem],
    summary="List all recommendations (admin)",
)
async def admin_recommendations(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[RecommendationHistoryItem]:
    result = await db.execute(
        select(Recommendation).order_by(Recommendation.created_at.desc()).limit(limit)
    )
    return [RecommendationHistoryItem.model_validate(r) for r in result.scalars().all()]


@router.get(
    "/simulations",
    response_model=list[ReviewSimulationHistoryItem],
    summary="List all review simulations (admin)",
)
async def admin_simulations(
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ReviewSimulationHistoryItem]:
    result = await db.execute(
        select(ReviewSimulation).order_by(ReviewSimulation.created_at.desc()).limit(limit)
    )
    return [ReviewSimulationHistoryItem.model_validate(r) for r in result.scalars().all()]
