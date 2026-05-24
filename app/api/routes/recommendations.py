from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.agents.recommendation_agent import RecommendationAgent
from app.api.helpers import to_agent_result_schema
from app.core.deps import get_current_user, get_recommendation_agent, get_recommendation_engine
from app.core.exceptions import NotFoundError
from app.domain.enums import RecommendationCategory
from app.models.user import User
from app.recommendations.engine import RecommendationEngine
from app.schemas.recommendation import (
    RecommendationGenerateRequest,
    RecommendationHelpfulResponse,
    RecommendationHistoryItem,
    RecommendationResponse,
    RecommendationResult,
    RecommendationSaveResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=RecommendationResult,
    summary="Generate personalized healthcare recommendation",
    description=(
        "Uses **profile**, **persona**, **memory**, and **imported context** to reason "
        "before recommending. Supports categories: health_apps, wellness_plans, "
        "productivity_wellness, sleep_improvement, hydration_improvement, stress_reduction."
    ),
)
async def generate_recommendation(
    data: RecommendationGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[RecommendationAgent, Depends(get_recommendation_agent)],
) -> RecommendationResult:
    result = await agent.run(current_user.id, data.category)
    return to_agent_result_schema(result, RecommendationResult)


@router.get(
    "/current",
    response_model=RecommendationResponse,
    summary="Get latest recommendation",
)
async def get_current_recommendation(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
    category: RecommendationCategory | None = Query(default=None),
) -> RecommendationResponse:
    rec = await engine.get_current(current_user.id, category=category)
    if not rec:
        raise NotFoundError(
            "No recommendation found. Call POST /recommendations/generate first.",
            details={"user_id": current_user.id},
        )
    return RecommendationResponse(
        category=RecommendationCategory(rec.category),
        recommendation=rec.recommendation,
        reasoning=rec.reasoning,
        confidence=rec.confidence,
    )


@router.get(
    "/history",
    response_model=list[RecommendationHistoryItem],
    summary="Get recommendation history",
)
async def get_recommendation_history(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
    category: RecommendationCategory | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[RecommendationHistoryItem]:
    records = await engine.get_history(
        current_user.id, category=category, limit=limit
    )
    return [RecommendationHistoryItem.from_orm(r) for r in records]


@router.post(
    "/{recommendation_id}/save",
    response_model=RecommendationSaveResponse,
    summary="Save recommendation to memory",
    description=(
        "Marks the recommendation as saved and stores it in behavioural memory "
        "under the recommendation category."
    ),
)
async def save_recommendation(
    recommendation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
) -> RecommendationSaveResponse:
    saved = await engine.save_recommendation(current_user.id, recommendation_id)
    if not saved:
        raise NotFoundError(
            "Recommendation not found",
            details={"recommendation_id": recommendation_id},
        )
    rec, memory_created = saved
    return RecommendationSaveResponse(
        id=rec.id,
        is_saved=True,
        memory_created=memory_created,
        message="Recommendation saved to your memory library",
    )


@router.post(
    "/{recommendation_id}/helpful",
    response_model=RecommendationHelpfulResponse,
    summary="Mark recommendation as helpful",
)
async def mark_recommendation_helpful(
    recommendation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
) -> RecommendationHelpfulResponse:
    rec = await engine.mark_helpful(current_user.id, recommendation_id)
    if not rec:
        raise NotFoundError(
            "Recommendation not found",
            details={"recommendation_id": recommendation_id},
        )
    return RecommendationHelpfulResponse(id=rec.id, marked_helpful=True)
