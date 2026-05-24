"""Agent Orchestrator — coordinates full recommendation pipeline."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.agents.behaviour_analysis_agent import BehaviourAnalysisAgent
from app.agents.memory_agent import MemoryAgent
from app.cold_start.engine import ColdStartEngine
from app.core.exceptions import NotFoundError
from app.domain.enums import OrchestrationStatus
from app.explanations.service import ExplanationService
from app.models.orchestration_run import OrchestrationRun
from app.models.recommendation_batch import RecommendationRankingBatch
from app.persona.engine import PersonaEngine
from app.nigerian_context.engine import NigerianContextEngine
from app.recommendations.cross_domain_engine import CrossDomainRecommendationEngine
from app.repositories.memory_repository import MemoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.agents import (
    CrossDomainRankRequest,
    OrchestrationRequest,
    OrchestrationResponse,
    OrchestrationStep,
)
from app.services.reasoning_service import ReasoningService

logger = logging.getLogger(__name__)

COLD_START_MEMORY_THRESHOLD = 2


class OrchestratorEngine:
    """
    Pipeline: Profile → Memory → Persona → Behaviour Analysis →
    Nigerian Context → Recommendation/Ranking → Reasoning Trace → Explanation
    """

    def __init__(
        self,
        db: AsyncSession,
        profile_repo: ProfileRepository,
        memory_repo: MemoryRepository,
        memory_agent: MemoryAgent,
        persona_engine: PersonaEngine,
        behaviour_agent: BehaviourAnalysisAgent,
        nigerian_engine: NigerianContextEngine,
        cross_domain_engine: CrossDomainRecommendationEngine,
        cold_start_engine: ColdStartEngine,
        explanation_service: ExplanationService,
        reasoning: ReasoningService,
    ) -> None:
        self._db = db
        self._profile_repo = profile_repo
        self._memory_repo = memory_repo
        self._memory_agent = memory_agent
        self._persona_engine = persona_engine
        self._behaviour_agent = behaviour_agent
        self._nigerian = nigerian_engine
        self._cross_domain = cross_domain_engine
        self._cold_start = cold_start_engine
        self._explanations = explanation_service
        self._reasoning = reasoning

    async def run(
        self, user_id: int, request: OrchestrationRequest | None = None
    ) -> AgentResult[OrchestrationResponse]:
        request = request or OrchestrationRequest()
        pipeline: list[OrchestrationStep] = []
        all_steps: list[str] = []

        profile = await self._profile_repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found. Complete onboarding first.")
        pipeline.append(
            OrchestrationStep(step="profile", status="completed", detail="Profile loaded")
        )
        all_steps.append("Retrieved user profile")

        memories = await self._memory_repo.list_by_user(user_id, limit=20)
        pipeline.append(
            OrchestrationStep(
                step="memory",
                status="completed",
                detail=f"{len(memories)} memory records",
            )
        )
        all_steps.append("Retrieved behavioural memory")

        use_cold_start = request.run_cold_start or len(memories) <= COLD_START_MEMORY_THRESHOLD
        persona_name: str | None = None
        ranking_batch_id: int | None = None
        explanation_id: int | None = None
        summary = ""

        if use_cold_start:
            cold_result = await self._cold_start.run(user_id)
            persona_name = cold_result.data.persona
            pipeline.append(
                OrchestrationStep(
                    step="cold_start",
                    status="completed",
                    detail=f"Persona: {persona_name}",
                )
            )
            all_steps.extend(cold_result.steps)
            summary = cold_result.data.reasoning
        else:
            persona_result = await self._persona_engine.generate(user_id)
            persona_name = persona_result.data.persona_name
            pipeline.append(
                OrchestrationStep(
                    step="persona_generation",
                    status="completed",
                    detail=persona_name,
                )
            )
            all_steps.extend(persona_result.steps)

        behaviour_result = await self._behaviour_agent.run(user_id)
        pipeline.append(
            OrchestrationStep(step="behaviour_analysis", status="completed")
        )
        all_steps.extend(behaviour_result.steps)

        nigerian_result = await self._nigerian.analyze(user_id)
        pipeline.append(
            OrchestrationStep(
                step="nigerian_context",
                status="completed",
                detail=nigerian_result.data.affordability_tier,
            )
        )
        all_steps.extend(nigerian_result.steps)

        concern = request.concern or profile.health_goals or "general wellness"
        if use_cold_start:
            pipeline.append(
                OrchestrationStep(
                    step="recommendation_generation",
                    status="completed",
                    detail="Cold-start recommendations stored",
                )
            )
        else:
            rank_result = await self._cross_domain.rank(
                user_id, CrossDomainRankRequest(concern=concern[:500])
            )
            ranking_batch_id = rank_result.data.batch_id
            summary = (
                f"Ranked {len(rank_result.data.ranked_recommendations)} cross-domain "
                f"recommendations for: {concern}"
            )
            pipeline.append(
                OrchestrationStep(step="ranking", status="completed", detail=summary)
            )
            all_steps.extend(rank_result.steps)

            from sqlalchemy import select

            stmt = select(RecommendationRankingBatch).where(
                RecommendationRankingBatch.id == ranking_batch_id
            )
            batch = (await self._db.execute(stmt)).scalar_one()

            persona_snap, mem_snippets, conf = await self._explanations.build_snapshot(
                user_id
            )
            avg_conf = (
                sum(r.confidence for r in rank_result.data.ranked_recommendations)
                / max(1, len(rank_result.data.ranked_recommendations))
            )
            explanation = await self._explanations.create_from_ranking(
                user_id,
                batch=batch,
                persona_name=persona_snap or persona_name or "",
                reasoning=rank_result.data.ranked_recommendations[0].reasoning
                if rank_result.data.ranked_recommendations
                else summary,
                memories=mem_snippets,
                confidence=round((conf + avg_conf) / 2, 3),
            )
            explanation_id = explanation.id
            pipeline.append(
                OrchestrationStep(
                    step="explanation",
                    status="completed",
                    detail=f"Explanation id={explanation_id}",
                )
            )

        pipeline.append(
            OrchestrationStep(step="reasoning_trace", status="completed")
        )
        await self._reasoning.save_trace(
            self._db, user_id, "orchestration", all_steps
        )

        run = OrchestrationRun(
            user_id=user_id,
            status=OrchestrationStatus.COMPLETED.value,
            pipeline_steps_json=json.dumps([s.model_dump() for s in pipeline]),
            result_summary=summary or "Orchestration completed",
            explanation_id=explanation_id,
            ranking_batch_id=ranking_batch_id,
        )
        self._db.add(run)
        await self._db.flush()

        response = OrchestrationResponse(
            run_id=run.id,
            status=run.status,
            pipeline=pipeline,
            persona_name=persona_name,
            ranking_batch_id=ranking_batch_id,
            explanation_id=explanation_id,
            summary=run.result_summary,
        )
        logger.info("Orchestration run %s for user %s", run.id, user_id)
        return AgentResult(data=response, steps=all_steps)
