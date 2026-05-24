"""Explanation API service — reasoning, memory, persona, confidence."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.enums import ExplanationEntityType
from app.models.cold_start_run import ColdStartRun
from app.models.explanation import Explanation
from app.models.recommendation import Recommendation
from app.models.recommendation_batch import RecommendationRankingBatch
from app.models.review_simulation import ReviewSimulation
from app.repositories.memory_repository import MemoryRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.explanations import ExplanationResponse

logger = logging.getLogger(__name__)


class ExplanationService:
    def __init__(
        self,
        db: AsyncSession,
        memory_repo: MemoryRepository,
        persona_repo: PersonaRepository,
    ) -> None:
        self._db = db
        self._memory_repo = memory_repo
        self._persona_repo = persona_repo

    async def get_by_id(self, user_id: int, explanation_id: int) -> ExplanationResponse:
        stmt = select(Explanation).where(
            Explanation.id == explanation_id,
            Explanation.user_id == user_id,
        )
        row = (await self._db.execute(stmt)).scalar_one_or_none()
        if not row:
            raise NotFoundError(
                "Explanation not found",
                details={"explanation_id": explanation_id},
            )
        memory = json.loads(row.memory_snapshot) if row.memory_snapshot else []
        return ExplanationResponse(
            id=row.id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            reasoning=row.reasoning,
            retrieved_memory=memory if isinstance(memory, list) else [],
            persona=row.persona_snapshot,
            confidence_score=row.confidence,
            created_at=row.created_at,
        )

    async def create_from_ranking(
        self,
        user_id: int,
        *,
        batch: RecommendationRankingBatch,
        persona_name: str,
        reasoning: str,
        memories: list[str],
        confidence: float,
    ) -> Explanation:
        explanation = Explanation(
            user_id=user_id,
            entity_type=ExplanationEntityType.RANKING_BATCH.value,
            entity_id=batch.id,
            reasoning=reasoning,
            memory_snapshot=json.dumps(memories[:10]),
            persona_snapshot=persona_name,
            confidence=confidence,
        )
        self._db.add(explanation)
        await self._db.flush()
        return explanation

    async def build_snapshot(self, user_id: int) -> tuple[str, list[str], float]:
        persona = await self._persona_repo.get_latest(user_id)
        persona_name = persona.persona_name if persona else "Unknown"
        confidence = persona.confidence_score if persona else 0.7

        memories = await self._memory_repo.list_by_user(user_id, limit=10)
        snippets = [m.content[:300] for m in memories]
        return persona_name, snippets, confidence
