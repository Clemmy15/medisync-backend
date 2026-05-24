"""Recommendation Agent — personalized healthcare recommendations with reasoning."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.domain.enums import MemoryCategory, RecommendationCategory
from app.memory.behavioural_engine import BehaviouralMemoryEngine
from app.models.recommendation import Recommendation
from app.persona.engine import PersonaEngine
from app.recommendations.context_builder import RecommendationContextBuilder
from app.repositories.context_import_repository import ContextImportRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import RecommendationResponse
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import RECOMMENDATION_SYSTEM

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates personalized recommendations using:
    - User profile
    - Current persona
    - Behavioural memory
    - Imported cross-AI context
    """

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        memory_engine: BehaviouralMemoryEngine,
        persona_engine: PersonaEngine,
        profile_repo: ProfileRepository,
        import_repo: ContextImportRepository,
        recommendation_repo: RecommendationRepository,
        reasoning: ReasoningService,
        analytics: AnalyticsService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._memory_engine = memory_engine
        self._persona_engine = persona_engine
        self._profile_repo = profile_repo
        self._import_repo = import_repo
        self._recommendation_repo = recommendation_repo
        self._reasoning = reasoning
        self._analytics = analytics

    async def generate(
        self,
        user_id: int,
        category: RecommendationCategory | None = None,
    ) -> AgentResult[RecommendationResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved user persona",
            "Retrieved behavioural memory",
            "Retrieved imported AI context",
        ]

        profile = await self._profile_repo.get_by_user_id(user_id)
        persona = await self._persona_engine.get_current(user_id)
        memories = await self._memory_engine.list_memories(user_id, limit=40)
        imports = await self._import_repo.list_by_user(user_id, limit=10)

        bundle = RecommendationContextBuilder.build(
            profile, persona, memories, imports, category
        )
        steps.append(
            f"Analyzed user context (sources: {', '.join(bundle.sources_used) or 'limited'})"
        )

        if category:
            steps.append(f"Focused recommendation category: {category.value}")
        else:
            steps.append("Selected optimal recommendation category")

        steps.append("Reasoned about user needs before recommending")
        steps.append("Matched recommendation to user context")

        context = bundle.full_context or "Limited user data available."
        result = await self._llm.complete_json(
            RECOMMENDATION_SYSTEM,
            (
                f"User data:\n{context}\n\n"
                "First reason about the user's needs, then provide one actionable "
                "personalized healthcare recommendation."
            ),
        )
        steps.append("Generated personalized recommendation response")

        response = self._build_response(result, bundle.data_richness_score, category)

        rec = Recommendation(
            user_id=user_id,
            category=response.category,
            recommendation=response.recommendation,
            reasoning=response.reasoning,
            confidence=response.confidence,
            sources_used=json.dumps(bundle.sources_used),
        )
        await self._recommendation_repo.create(rec)
        await self._db.refresh(rec)

        await self._reasoning.save_trace(
            self._db, user_id, "recommendation", steps, reference_id=rec.id
        )
        await self._analytics.track_event(self._db, "recommendation_generated", user_id)

        logger.info(
            "Recommendation [%s] for user %s confidence=%.2f",
            response.category,
            user_id,
            response.confidence,
        )
        return AgentResult(data=response, steps=steps)

    async def get_history(
        self,
        user_id: int,
        *,
        category: RecommendationCategory | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        return await self._recommendation_repo.list_by_user(
            user_id, category=category, limit=limit
        )

    async def get_current(
        self,
        user_id: int,
        category: RecommendationCategory | None = None,
    ) -> Recommendation | None:
        return await self._recommendation_repo.get_latest(user_id, category=category)

    async def get_by_id(self, user_id: int, rec_id: int) -> Recommendation | None:
        return await self._recommendation_repo.get_by_id(rec_id, user_id)

    async def save_recommendation(
        self, user_id: int, rec_id: int, *, persist_memory: bool = True
    ) -> tuple[Recommendation, bool] | None:
        rec = await self._recommendation_repo.get_by_id(rec_id, user_id)
        if not rec:
            return None

        rec.is_saved = True
        memory_created = False
        if persist_memory:
            content = (
                f"[saved recommendation · {rec.category}] {rec.recommendation} "
                f"(Reasoning: {rec.reasoning})"
            )
            await self._memory_engine.create(
                user_id, MemoryCategory.RECOMMENDATION, content[:10000]
            )
            memory_created = True

        await self._db.flush()
        return rec, memory_created

    async def mark_helpful(self, user_id: int, rec_id: int) -> Recommendation | None:
        rec = await self._recommendation_repo.get_by_id(rec_id, user_id)
        if not rec:
            return None
        rec.marked_helpful = True
        await self._db.flush()
        await self._analytics.track_event(self._db, "recommendation_helpful", user_id)
        return rec

    @staticmethod
    def _build_response(
        llm_result: dict,
        data_richness: float,
        requested_category: RecommendationCategory | None,
    ) -> RecommendationResponse:
        rec_text = str(llm_result.get("recommendation", ""))
        reasoning = str(llm_result.get("reasoning", ""))

        raw_category = llm_result.get("category") or (
            requested_category.value if requested_category else None
        )
        try:
            cat = RecommendationCategory(raw_category) if raw_category else (
                requested_category or RecommendationCategory.WELLNESS_PLANS
            )
        except ValueError:
            cat = requested_category or RecommendationCategory.WELLNESS_PLANS

        llm_conf = llm_result.get("confidence")
        if llm_conf is not None:
            confidence = round(0.65 * float(llm_conf) + 0.35 * data_richness, 3)
        else:
            confidence = round(max(0.55, data_richness * 0.88), 3)

        confidence = max(0.0, min(1.0, confidence))

        return RecommendationResponse(
            category=cat,
            recommendation=rec_text,
            reasoning=reasoning,
            confidence=confidence,
        )
