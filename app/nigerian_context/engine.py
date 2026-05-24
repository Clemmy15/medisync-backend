"""Nigerian Context Reasoning Layer — affordability, lifestyle, communication style."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.core.exceptions import NotFoundError
from app.models.nigerian_context import NigerianContextRecord
from app.repositories.profile_repository import ProfileRepository
from app.schemas.agents import NigerianContextResponse
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import NIGERIAN_CONTEXT_SYSTEM

logger = logging.getLogger(__name__)


class NigerianContextEngine:
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

    async def analyze(self, user_id: int) -> AgentResult[NigerianContextResponse]:
        profile = await self._profile_repo.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found. Complete onboarding first.")

        context = (
            f"Age: {profile.age_range}\n"
            f"Occupation: {profile.occupation}\n"
            f"Goals: {profile.health_goals}\n"
            f"Activity: {profile.activity_level}\n"
            f"Stress: {profile.stress_level}\n"
            f"Sleep: {profile.sleep_pattern}\n"
            f"Communication: {profile.communication_style}\n"
        )
        steps = [
            "Loaded user profile for Nigerian context",
            "Applied affordability and student budget reasoning",
            "Derived local lifestyle and communication patterns",
        ]

        result = await self._llm.complete_json(
            NIGERIAN_CONTEXT_SYSTEM,
            f"Adapt guidance for this Nigerian user:\n{context}",
        )

        record = NigerianContextRecord(
            user_id=user_id,
            affordability_tier=str(result.get("affordability_tier", "student_budget")),
            affordability_notes=str(result.get("affordability_notes", "")),
            lifestyle_patterns=str(result.get("lifestyle_patterns", "")),
            communication_style=str(result.get("communication_style", "")),
            contextual_reasoning=str(result.get("contextual_reasoning", "")),
        )
        self._db.add(record)
        await self._db.flush()

        await self._reasoning.save_trace(
            self._db, user_id, "nigerian_context", steps, reference_id=record.id
        )

        response = NigerianContextResponse(
            affordability_tier=record.affordability_tier,
            affordability_notes=record.affordability_notes,
            lifestyle_patterns=record.lifestyle_patterns,
            communication_style=record.communication_style,
            contextual_reasoning=record.contextual_reasoning,
            record_id=record.id,
        )
        logger.info("Nigerian context record %s for user %s", record.id, user_id)
        return AgentResult(data=response, steps=steps)

    async def get_latest(self, user_id: int) -> NigerianContextRecord | None:
        from sqlalchemy import select

        stmt = (
            select(NigerianContextRecord)
            .where(NigerianContextRecord.user_id == user_id)
            .order_by(NigerianContextRecord.created_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def adapt_prompt_suffix(self, record: NigerianContextRecord | None) -> str:
        if not record:
            return ""
        return (
            f"\nNigerian context ({record.affordability_tier}): "
            f"{record.contextual_reasoning} "
            f"Style: {record.communication_style}"
        )
