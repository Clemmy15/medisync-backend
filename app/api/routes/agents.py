from typing import Annotated

from fastapi import APIRouter, Depends

from app.agents.cold_start_agent import ColdStartAgent
from app.api.helpers import to_agent_result_schema
from app.core.deps import (
    get_cold_start_agent,
    get_cross_domain_engine,
    get_current_user,
    get_nigerian_context_engine,
    get_orchestrator_engine,
)
from app.models.user import User
from app.nigerian_context.engine import NigerianContextEngine
from app.orchestrator.engine import OrchestratorEngine
from app.recommendations.cross_domain_engine import CrossDomainRecommendationEngine
from app.schemas.agents import (
    ColdStartRequest,
    ColdStartResult,
    CrossDomainRankRequest,
    CrossDomainRankResult,
    NigerianContextResponse,
    OrchestrationRequest,
    OrchestrationResult,
)

router = APIRouter()


@router.post(
    "/cold-start",
    response_model=ColdStartResult,
    summary="Cold Start Agent — recommendations for new users",
)
async def cold_start(
    data: ColdStartRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[ColdStartAgent, Depends(get_cold_start_agent)],
) -> ColdStartResult:
    result = await agent.run(current_user.id, data)
    return to_agent_result_schema(result, ColdStartResult)


@router.post(
    "/cross-domain/rank",
    response_model=CrossDomainRankResult,
    summary="Cross-domain recommendation ranking",
)
async def cross_domain_rank(
    data: CrossDomainRankRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[
        CrossDomainRecommendationEngine, Depends(get_cross_domain_engine)
    ],
) -> CrossDomainRankResult:
    result = await engine.rank(current_user.id, data)
    return to_agent_result_schema(result, CrossDomainRankResult)


@router.post(
    "/nigerian-context",
    response_model=NigerianContextResponse,
    summary="Nigerian Context Reasoning Layer",
)
async def nigerian_context(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[NigerianContextEngine, Depends(get_nigerian_context_engine)],
) -> NigerianContextResponse:
    result = await engine.analyze(current_user.id)
    return result.data


@router.post(
    "/orchestrate",
    response_model=OrchestrationResult,
    summary="Agent Orchestrator — full pipeline",
    description=(
        "Coordinates: Profile → Memory → Persona → Behaviour Analysis → "
        "Nigerian Context → Ranking → Reasoning Trace → Explanation"
    ),
)
async def orchestrate(
    data: OrchestrationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[OrchestratorEngine, Depends(get_orchestrator_engine)],
) -> OrchestrationResult:
    result = await engine.run(current_user.id, data)
    return to_agent_result_schema(result, OrchestrationResult)
