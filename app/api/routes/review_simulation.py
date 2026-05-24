from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.agents.review_simulation_agent import ReviewSimulationAgent
from app.core.deps import (
    get_current_user,
    get_review_simulation_agent,
    get_review_simulation_engine,
)
from app.core.exceptions import NotFoundError
from app.domain.enums import SimulationTargetType
from app.models.user import User
from app.review_simulation.engine import ReviewSimulationEngine
from app.api.helpers import to_agent_result_schema
from app.schemas.review_simulation import (
    ReviewSimulationHistoryItem,
    ReviewSimulationRequest,
    ReviewSimulationResponse,
    ReviewSimulationResult,
)

router = APIRouter()


@router.post(
    "/review",
    response_model=ReviewSimulationResult,
    summary="Simulate persona-based product/service review (Hackathon Task A)",
    description=(
        "Simulates realistic **ratings**, **reviews**, and **behavioural reasoning** "
        "from a user persona. Supports healthcare apps, wellness products, "
        "telemedicine services, pharmacies, and fitness programs."
    ),
)
async def simulate_review(
    data: ReviewSimulationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[ReviewSimulationAgent, Depends(get_review_simulation_agent)],
) -> ReviewSimulationResult:
    result = await agent.run(current_user.id, data)
    return to_agent_result_schema(result, ReviewSimulationResult)


@router.get(
    "/history",
    response_model=list[ReviewSimulationHistoryItem],
    summary="Get review simulation history",
)
async def get_simulation_history(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[ReviewSimulationEngine, Depends(get_review_simulation_engine)],
    target_type: SimulationTargetType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ReviewSimulationHistoryItem]:
    records = await engine.get_history(
        current_user.id, target_type=target_type, limit=limit
    )
    return [ReviewSimulationHistoryItem.model_validate(r) for r in records]


@router.get(
    "/current",
    response_model=ReviewSimulationResponse,
    summary="Get latest review simulation",
)
async def get_current_simulation(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[ReviewSimulationEngine, Depends(get_review_simulation_engine)],
    target_type: SimulationTargetType | None = Query(default=None),
) -> ReviewSimulationResponse:
    rec = await engine.get_current(current_user.id, target_type=target_type)
    if not rec:
        raise NotFoundError(
            "No review simulation found. Call POST /simulation/review first.",
        )
    return ReviewSimulationResponse(
        rating=rec.rating,
        review=rec.review,
        reasoning=rec.reasoning,
        persona_name=rec.persona_name,
        target_type=SimulationTargetType(rec.target_type),
    )
