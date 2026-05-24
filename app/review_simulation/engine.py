"""Review Simulation Engine — persona-based product/service review simulation."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.core.exceptions import NotFoundError
from app.domain.enums import SimulationTargetType
from app.models.review_simulation import ReviewSimulation
from app.persona.engine import PersonaEngine
from app.repositories.review_simulation_repository import ReviewSimulationRepository
from app.review_simulation.context_builder import ReviewSimulationContextBuilder
from app.schemas.review_simulation import ReviewSimulationRequest, ReviewSimulationResponse
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import REVIEW_SIMULATION_SYSTEM

logger = logging.getLogger(__name__)


class ReviewSimulationEngine:
    """
    Simulates realistic ratings and reviews from a user persona's perspective.

    Supports: healthcare apps, wellness products, telemedicine services,
    pharmacies, and fitness programs.
    """

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        persona_engine: PersonaEngine,
        simulation_repo: ReviewSimulationRepository,
        reasoning: ReasoningService,
        analytics: AnalyticsService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._persona_engine = persona_engine
        self._simulation_repo = simulation_repo
        self._reasoning = reasoning
        self._analytics = analytics

    async def simulate(
        self,
        user_id: int,
        request: ReviewSimulationRequest,
    ) -> AgentResult[ReviewSimulationResponse]:
        steps = ["Loaded user persona context"]

        persona = await self._resolve_persona(user_id, request)
        steps.append(f"Identified target type: {request.target_type.value}")

        if request.product_description:
            steps.append("Analyzed product description")
        if request.service_description:
            steps.append("Analyzed service description")

        steps.append("Applied behavioural reasoning for rating expectations")
        steps.append("Simulated realistic review language")

        context = ReviewSimulationContextBuilder.build(
            persona=persona,
            persona_name=request.persona_name or (persona.persona_name if persona else ""),
            persona_reasoning=(
                persona.persona_reasoning if persona else request.persona_reasoning or ""
            ),
            product_description=request.product_description,
            service_description=request.service_description,
            target_type=request.target_type,
        )

        result = await self._llm.complete_json(
            REVIEW_SIMULATION_SYSTEM,
            context.llm_prompt,
        )
        steps.append("Generated rating, review, and behavioural reasoning")

        response = self._build_response(
            result,
            persona_name=context.persona_name,
            target_type=request.target_type,
        )

        simulation = ReviewSimulation(
            user_id=user_id,
            persona_name=context.persona_name,
            target_type=request.target_type.value,
            product_description=request.product_description,
            service_description=request.service_description,
            rating=response.rating,
            review=response.review,
            reasoning=response.reasoning,
        )
        await self._simulation_repo.create(simulation)
        await self._db.refresh(simulation)

        await self._reasoning.save_trace(
            self._db, user_id, "review_simulation", steps, reference_id=simulation.id
        )
        await self._analytics.track_event(self._db, "review_simulated", user_id)

        logger.info(
            "Review simulation [%s] persona=%s rating=%d user=%s",
            request.target_type.value,
            context.persona_name,
            response.rating,
            user_id,
        )
        return AgentResult(data=response, steps=steps)

    async def _resolve_persona(
        self, user_id: int, request: ReviewSimulationRequest
    ):
        if request.persona_name:
            history = await self._persona_engine.get_history(user_id, limit=20)
            for p in history:
                if p.persona_name.lower() == request.persona_name.lower():
                    return p
            if request.persona_reasoning:
                return None
            raise NotFoundError(
                f"Persona '{request.persona_name}' not found. "
                "Generate one via POST /persona/generate or provide persona_reasoning.",
                details={"persona_name": request.persona_name},
            )

        persona = await self._persona_engine.get_current(user_id)
        if persona:
            return persona
        if request.persona_reasoning:
            return None
        raise NotFoundError(
            "No persona found. Provide persona_name, persona_reasoning, "
            "or generate via POST /persona/generate.",
        )

    async def get_history(
        self,
        user_id: int,
        *,
        target_type: SimulationTargetType | None = None,
        limit: int = 50,
    ) -> list[ReviewSimulation]:
        return await self._simulation_repo.list_by_user(
            user_id, target_type=target_type, limit=limit
        )

    async def get_current(
        self,
        user_id: int,
        target_type: SimulationTargetType | None = None,
    ) -> ReviewSimulation | None:
        return await self._simulation_repo.get_latest(user_id, target_type=target_type)

    @staticmethod
    def _build_response(
        llm_result: dict,
        *,
        persona_name: str,
        target_type: SimulationTargetType,
    ) -> ReviewSimulationResponse:
        rating = int(llm_result.get("rating", 4))
        rating = max(1, min(5, rating))
        return ReviewSimulationResponse(
            rating=rating,
            review=str(llm_result.get("review", "")),
            reasoning=str(llm_result.get("reasoning", "")),
            persona_name=persona_name,
            target_type=target_type,
        )
