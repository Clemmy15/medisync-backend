"""Cold Start Agent — recommendations for users with little or no history."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.core.exceptions import NotFoundError
from app.domain.enums import RecommendationCategory
from app.models.cold_start_run import ColdStartRun
from app.models.recommendation import Recommendation
from app.repositories.profile_repository import ProfileRepository
from app.schemas.agents import (
    ColdStartRecommendationItem,
    ColdStartRequest,
    ColdStartResponse,
)
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import COLD_START_SYSTEM

logger = logging.getLogger(__name__)


class ColdStartEngine:
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        profile_repo: ProfileRepository,
        reasoning: ReasoningService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._profile_repo = profile_repo
        self._reasoning = reasoning

    async def run(
        self, user_id: int, request: ColdStartRequest | None = None
    ) -> AgentResult[ColdStartResponse]:
        request = request or ColdStartRequest()
        profile = await self._profile_repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found. Complete onboarding first.")

        context = self._build_context(profile, request)
        steps = [
            "Loaded onboarding profile (cold start — no memory required)",
            "Inferred persona from goals and lifestyle",
            "Generated cross-domain starter recommendations",
        ]

        result = await self._llm.complete_json(
            COLD_START_SYSTEM,
            f"New user onboarding data:\n{context}",
        )

        persona = str(result.get("persona", "New Wellness User"))
        reasoning = str(result.get("reasoning", ""))
        items = self._parse_recommendations(result.get("recommendations", []))

        run = ColdStartRun(
            user_id=user_id,
            persona=persona,
            recommendations_json=json.dumps([i.model_dump() for i in items]),
            reasoning=reasoning,
        )
        self._db.add(run)
        await self._db.flush()

        for item in items:
            rec = Recommendation(
                user_id=user_id,
                category=item.category.value,
                recommendation=item.recommendation,
                reasoning=reasoning,
                confidence=item.confidence,
                sources_used=json.dumps(["cold_start", "onboarding"]),
            )
            self._db.add(rec)

        await self._reasoning.save_trace(
            self._db, user_id, "cold_start", steps, reference_id=run.id
        )
        await self._db.flush()

        response = ColdStartResponse(
            persona=persona,
            recommendations=items,
            reasoning=reasoning,
            cold_start_id=run.id,
        )
        logger.info("Cold start run %s for user %s", run.id, user_id)
        return AgentResult(data=response, steps=steps)

    @staticmethod
    def _build_context(profile: object, request: ColdStartRequest) -> str:
        parts = [
            f"Age range: {getattr(request, 'age_range', None) or profile.age_range}",
            f"Occupation: {getattr(request, 'occupation', None) or profile.occupation}",
            f"Health goals: {getattr(request, 'health_goals', None) or profile.health_goals}",
            f"Activity: {getattr(request, 'activity_level', None) or profile.activity_level}",
            f"Stress: {getattr(request, 'stress_level', None) or profile.stress_level}",
            f"Sleep: {getattr(request, 'sleep_pattern', None) or profile.sleep_pattern}",
            f"Diet: {profile.dietary_preferences}",
            f"Communication: {profile.communication_style}",
        ]
        return "\n".join(parts)

    @staticmethod
    def _parse_recommendations(raw: object) -> list[ColdStartRecommendationItem]:
        if not isinstance(raw, list):
            return []
        items: list[ColdStartRecommendationItem] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            try:
                cat = RecommendationCategory(entry.get("category", "wellness_products"))
            except ValueError:
                cat = RecommendationCategory.WELLNESS_PRODUCTS
            items.append(
                ColdStartRecommendationItem(
                    category=cat,
                    recommendation=str(entry.get("recommendation", "")),
                    confidence=float(entry.get("confidence", 0.75)),
                )
            )
        return items
