"""Cross-Domain Recommendation Agent — rank recommendations across categories."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.domain.enums import RecommendationCategory
from app.evaluation.metrics import build_ranking_metrics
from app.models.recommendation import Recommendation
from app.models.recommendation_batch import RecommendationRankingBatch
from app.nigerian_context.engine import NigerianContextEngine
from app.repositories.profile_repository import ProfileRepository
from app.schemas.agents import (
    CrossDomainRankRequest,
    CrossDomainRankResponse,
    RankedRecommendationItem,
    RankingMetrics,
)
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import CROSS_DOMAIN_RANKING_SYSTEM

logger = logging.getLogger(__name__)


class CrossDomainRecommendationEngine:
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        profile_repo: ProfileRepository,
        nigerian_engine: NigerianContextEngine,
        reasoning: ReasoningService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._profile_repo = profile_repo
        self._nigerian = nigerian_engine
        self._reasoning = reasoning

    async def rank(
        self, user_id: int, request: CrossDomainRankRequest
    ) -> AgentResult[CrossDomainRankResponse]:
        profile = await self._profile_repo.get_by_user_id(user_id)
        nigerian = await self._nigerian.get_latest(user_id)
        nigerian_suffix = self._nigerian.adapt_prompt_suffix(nigerian)

        profile_ctx = ""
        if profile:
            profile_ctx = (
                f"Profile: occupation={profile.occupation}, "
                f"goals={profile.health_goals}, sleep={profile.sleep_pattern}"
            )

        steps = [
            "Loaded profile and Nigerian context layer",
            f"Analyzed concern: {request.concern}",
            "Generated cross-domain ranked recommendations",
            "Computed NDCG@10, hit rate, and diversity metrics",
        ]

        result = await self._llm.complete_json(
            CROSS_DOMAIN_RANKING_SYSTEM,
            (
                f"User concern: {request.concern}\n{profile_ctx}"
                f"{nigerian_suffix}\n"
                "Rank recommendations across health_apps, wellness_products, "
                "educational_content, food_nutrition, exercise_plans, "
                "productivity_habits, telemedicine_services."
            ),
        )

        ranked = self._parse_ranked(result.get("ranked_recommendations", []))
        metrics_dict = build_ranking_metrics(
            [{"category": r.category.value, "confidence": r.confidence} for r in ranked]
        )
        metrics = RankingMetrics(**metrics_dict)

        batch = RecommendationRankingBatch(
            user_id=user_id,
            concern=request.concern,
            ranked_items_json=json.dumps([r.model_dump() for r in ranked]),
            ranking_metrics_json=json.dumps(metrics_dict),
            nigerian_context_id=nigerian.id if nigerian else None,
        )
        self._db.add(batch)
        await self._db.flush()

        for item in ranked:
            rec = Recommendation(
                user_id=user_id,
                category=item.category.value,
                recommendation=item.recommendation,
                reasoning=item.reasoning,
                confidence=item.confidence,
                sources_used=json.dumps(["cross_domain_rank", request.concern]),
            )
            self._db.add(rec)

        await self._reasoning.save_trace(
            self._db, user_id, "cross_domain_rank", steps, reference_id=batch.id
        )
        await self._db.flush()

        response = CrossDomainRankResponse(
            concern=request.concern,
            ranked_recommendations=ranked,
            ranking_metrics=metrics,
            batch_id=batch.id,
        )
        logger.info("Cross-domain batch %s for user %s", batch.id, user_id)
        return AgentResult(data=response, steps=steps)

    @staticmethod
    def _parse_ranked(raw: object) -> list[RankedRecommendationItem]:
        if not isinstance(raw, list):
            return []
        items: list[RankedRecommendationItem] = []
        for idx, entry in enumerate(raw, start=1):
            if not isinstance(entry, dict):
                continue
            try:
                cat = RecommendationCategory(entry.get("category", "health_apps"))
            except ValueError:
                cat = RecommendationCategory.HEALTH_APPS
            items.append(
                RankedRecommendationItem(
                    rank=idx,
                    category=cat,
                    recommendation=str(entry.get("recommendation", "")),
                    reasoning=str(entry.get("reasoning", "")),
                    confidence=float(entry.get("confidence", 0.75)),
                )
            )
        return items
