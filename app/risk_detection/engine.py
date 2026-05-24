"""Risk Detection Engine — symptom patterns, deterioration, recurring concerns."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.domain.enums import RiskLevel
from app.memory.behavioural_engine import BehaviouralMemoryEngine
from app.models.risk_assessment import RiskAssessment
from app.persona.engine import PersonaEngine
from app.repositories.context_import_repository import ContextImportRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.risk_detection.context_builder import RiskContextBuilder
from app.schemas.risk_detection import RiskDetectionRequest, RiskDetectionResponse
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import RISK_DETECTION_SYSTEM

logger = logging.getLogger(__name__)

_RISK_ALIASES: dict[str, RiskLevel] = {
    "low": RiskLevel.LOW,
    "moderate": RiskLevel.MODERATE,
    "medium": RiskLevel.MODERATE,
    "high": RiskLevel.HIGH,
    "critical": RiskLevel.HIGH,
    "emergency": RiskLevel.HIGH,
}


class RiskDetectionEngine:
    """
    Detects health risks by analyzing:
    - Dangerous symptom patterns
    - Behavioural deterioration
    - Recurring health concerns
    """

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        memory_engine: BehaviouralMemoryEngine,
        persona_engine: PersonaEngine,
        profile_repo: ProfileRepository,
        import_repo: ContextImportRepository,
        assessment_repo: RiskAssessmentRepository,
        reasoning: ReasoningService,
        analytics: AnalyticsService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._memory_engine = memory_engine
        self._persona_engine = persona_engine
        self._profile_repo = profile_repo
        self._import_repo = import_repo
        self._assessment_repo = assessment_repo
        self._reasoning = reasoning
        self._analytics = analytics

    async def detect(
        self,
        user_id: int,
        request: RiskDetectionRequest,
    ) -> AgentResult[RiskDetectionResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved behavioural memory",
            "Retrieved imported AI context",
        ]

        profile = await self._profile_repo.get_by_user_id(user_id)
        persona = await self._persona_engine.get_current(user_id)
        memories = await self._memory_engine.list_memories(user_id, limit=50)
        imports = await self._import_repo.list_by_user(user_id, limit=10)

        bundle = RiskContextBuilder.build(
            profile,
            persona,
            memories,
            imports,
            request.symptoms,
            request.context,
        )
        steps.append("Identified dangerous symptom patterns")
        steps.append("Identified behavioural deterioration")
        steps.append("Identified recurring health concerns")

        context = bundle.full_context or "Limited user data available."
        user_prompt = (
            f"{context}\n\n"
            "Assess overall health risk. Consider symptom severity, worsening trends, "
            "and repeated concerns across memory and imports. "
            "Never replace emergency services for acute danger."
        )

        result = await self._llm.complete_json(RISK_DETECTION_SYSTEM, user_prompt)
        steps.append("Assessed risk level and recommended action")

        response = self._build_response(result)

        assessment = RiskAssessment(
            user_id=user_id,
            risk_level=response.risk_level.value,
            reasoning=response.reasoning,
            recommended_action=response.recommended_action,
            reported_symptoms=json.dumps(request.symptoms) if request.symptoms else None,
        )
        await self._assessment_repo.create(assessment)
        await self._db.refresh(assessment)

        await self._reasoning.save_trace(
            self._db, user_id, "risk_detection", steps, reference_id=assessment.id
        )
        await self._analytics.track_event(self._db, "risk_assessed", user_id)

        logger.info(
            "Risk assessment [%s] for user %s id=%s",
            response.risk_level.value,
            user_id,
            assessment.id,
        )
        return AgentResult(data=response, steps=steps)

    async def get_history(
        self, user_id: int, *, limit: int = 50
    ) -> list[RiskAssessment]:
        return await self._assessment_repo.list_by_user(user_id, limit=limit)

    async def get_current(self, user_id: int) -> RiskAssessment | None:
        return await self._assessment_repo.get_latest(user_id)

    @staticmethod
    def _build_response(llm_result: dict) -> RiskDetectionResponse:
        raw = str(llm_result.get("risk_level", "low")).lower().strip()
        risk_level = _RISK_ALIASES.get(raw, RiskLevel.LOW)
        return RiskDetectionResponse(
            risk_level=risk_level,
            reasoning=str(llm_result.get("reasoning", "")),
            recommended_action=str(llm_result.get("recommended_action", "")),
        )
