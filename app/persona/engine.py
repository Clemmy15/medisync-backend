"""User Persona Engine — generates behavioural personas from multi-source context."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.memory.behavioural_engine import BehaviouralMemoryEngine
from app.models.persona import Persona
from app.persona.context_builder import PersonaContextBuilder
from app.persona.templates import CANONICAL_PERSONAS
from app.repositories.context_import_repository import ContextImportRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.persona import PersonaGenerateResponse
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService
from app.utils.prompts import PERSONA_SYSTEM

logger = logging.getLogger(__name__)


class PersonaEngine:
    """
    Generates user behavioural personas from:
    - Profile data
    - Behavioural memory (PostgreSQL + ChromaDB)
    - Imported cross-AI context
    - Derived behavioural patterns
    """

    def __init__(
        self,
        db: AsyncSession,
        llm: LLMService,
        memory_engine: BehaviouralMemoryEngine,
        profile_repo: ProfileRepository,
        import_repo: ContextImportRepository,
        persona_repo: PersonaRepository,
        reasoning: ReasoningService,
    ) -> None:
        self._db = db
        self._llm = llm
        self._memory_engine = memory_engine
        self._profile_repo = profile_repo
        self._import_repo = import_repo
        self._persona_repo = persona_repo
        self._reasoning = reasoning

    async def generate(self, user_id: int) -> AgentResult[PersonaGenerateResponse]:
        steps = [
            "Retrieved user profile",
            "Retrieved behavioural memory",
            "Retrieved imported AI context",
            "Analyzed behavioural patterns",
        ]

        profile = await self._profile_repo.get_by_user_id(user_id)
        memories = await self._memory_engine.list_memories(user_id, limit=50)
        imports = await self._import_repo.list_by_user(user_id, limit=10)

        bundle = PersonaContextBuilder.build(profile, memories, imports)
        steps.append(
            f"Aggregated sources: {', '.join(bundle.sources_used) or 'none'}"
        )

        context = bundle.full_context or "No user data available yet."
        personas_list = ", ".join(CANONICAL_PERSONAS)

        result = await self._llm.complete_json(
            PERSONA_SYSTEM,
            (
                f"Canonical personas (prefer one of these): {personas_list}\n\n"
                f"User data:\n{context}\n\n"
                "Classify the user into the best-matching behavioural persona."
            ),
        )
        steps.append("Generated persona classification")

        response = self._build_response(result, bundle.data_richness_score)

        persona = Persona(
            user_id=user_id,
            persona_name=response.persona_name,
            persona_reasoning=response.reasoning,
            confidence_score=response.confidence_score,
            sources_used=json.dumps(bundle.sources_used),
        )
        await self._persona_repo.create(persona)
        await self._db.refresh(persona)

        await self._reasoning.save_trace(
            self._db, user_id, "persona", steps, reference_id=persona.id
        )

        logger.info(
            "Generated persona '%s' for user %s (confidence=%.2f)",
            response.persona_name,
            user_id,
            response.confidence_score,
        )
        return AgentResult(data=response, steps=steps)

    async def get_history(self, user_id: int, limit: int = 20) -> list[Persona]:
        return await self._persona_repo.list_by_user(user_id, limit=limit)

    async def get_current(self, user_id: int) -> Persona | None:
        return await self._persona_repo.get_latest(user_id)

    @staticmethod
    def _build_response(
        llm_result: dict,
        data_richness: float,
    ) -> PersonaGenerateResponse:
        name = str(
            llm_result.get("persona_name")
            or llm_result.get("name")
            or "Young Professional"
        )
        reasoning = str(
            llm_result.get("reasoning")
            or llm_result.get("persona_reasoning")
            or ""
        )
        llm_conf = llm_result.get("confidence_score") or llm_result.get("confidence")
        if llm_conf is not None:
            confidence = float(llm_conf)
            # Blend with data richness so sparse profiles get lower scores
            confidence = round(0.6 * confidence + 0.4 * data_richness, 3)
        else:
            confidence = round(max(0.5, data_richness * 0.9), 3)

        confidence = max(0.0, min(1.0, confidence))
        return PersonaGenerateResponse(
            persona_name=name,
            reasoning=reasoning,
            confidence_score=confidence,
        )
