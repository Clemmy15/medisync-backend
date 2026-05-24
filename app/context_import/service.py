import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentResult
from app.agents.memory_agent import MemoryAgent
from app.context_import.extractor import ContextExtractor
from app.context_import.prompts import (
    get_all_platform_prompts,
    get_import_instructions,
    get_import_prompt,
)
from app.domain.enums import AIPlatform
from app.models.context_import import ContextImport
from app.repositories.context_import_repository import ContextImportRepository
from app.schemas.context_import import (
    ContextExtractionResponse,
    ContextSaveResponse,
    ImportPromptResponse,
    PlatformPromptItem,
    PlatformPromptsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.reasoning_service import ReasoningService
from app.utils.json_helpers import safe_json_dumps

logger = logging.getLogger(__name__)


class ContextImportService:
    def __init__(
        self,
        db: AsyncSession,
        extractor: ContextExtractor,
        memory_agent: MemoryAgent,
        import_repo: ContextImportRepository,
        analytics: AnalyticsService,
        reasoning: ReasoningService | None = None,
    ) -> None:
        self._db = db
        self._extractor = extractor
        self._memory_agent = memory_agent
        self._import_repo = import_repo
        self._analytics = analytics
        self._reasoning = reasoning or ReasoningService()

    def get_all_prompts(self) -> PlatformPromptsResponse:
        items = [
            PlatformPromptItem(
                platform=platform,
                prompt=data["prompt"],
                instructions=data["instructions"],
            )
            for platform, data in get_all_platform_prompts().items()
        ]
        return PlatformPromptsResponse(platforms=items)

    def get_platform_prompt(self, platform: AIPlatform) -> ImportPromptResponse:
        return ImportPromptResponse(
            platform=platform,
            prompt=get_import_prompt(platform),
            instructions=get_import_instructions(platform),
        )

    async def analyze(
        self,
        content: str,
        source_platform: AIPlatform | None = None,
        *,
        user_id: int | None = None,
    ) -> AgentResult[ContextExtractionResponse]:
        steps = [
            "Parsed imported AI context text",
            "Extracted structured health fields",
            "Computed per-field confidence scores",
            "Generated narrative summary",
        ]
        extraction = await self._extractor.extract(content, source_platform)
        if user_id is not None:
            await self._reasoning.save_trace(
                self._db, user_id, "context_analyze", steps
            )
        return AgentResult(data=extraction, steps=steps)

    async def save(
        self,
        user_id: int,
        content: str,
        source_platform: AIPlatform | None = None,
        pre_extracted: ContextExtractionResponse | None = None,
    ) -> AgentResult[ContextSaveResponse]:
        steps: list[str] = []
        if pre_extracted is not None:
            extraction = pre_extracted
            steps.append("Used pre-analyzed extraction")
        else:
            analyze_result = await self.analyze(
                content, source_platform, user_id=user_id
            )
            extraction = analyze_result.data
            steps.extend(analyze_result.steps)

        payload = extraction.model_dump()
        record = ContextImport(
            user_id=user_id,
            source_platform=source_platform.value if source_platform else None,
            raw_content=content,
            extracted_data=safe_json_dumps(payload),
            confidence_score=extraction.confidence,
            field_confidence=safe_json_dumps(
                extraction.field_confidence.model_dump()
            ),
            summary=extraction.summary,
        )
        await self._import_repo.create(record)

        steps.append("Persisted context to PostgreSQL")
        memories_created = await self._persist_to_memory(user_id, extraction)
        steps.append("Indexed memories in ChromaDB")
        steps.append("Generated response")

        await self._analytics.track_event(self._db, "context_imported", user_id)
        await self._reasoning.save_trace(
            self._db, user_id, "context_save", steps, reference_id=record.id
        )
        logger.info(
            "Saved context import id=%s user_id=%s memories=%d confidence=%.2f",
            record.id,
            user_id,
            memories_created,
            extraction.confidence,
        )

        response = ContextSaveResponse(
            id=record.id,
            message="Context saved to PostgreSQL and ChromaDB memory",
            extraction=extraction,
            memories_created=memories_created,
        )
        return AgentResult(data=response, steps=steps)

    async def _persist_to_memory(
        self, user_id: int, extraction: ContextExtractionResponse
    ) -> int:
        """Write extracted items to dual memory store (PostgreSQL + ChromaDB)."""
        mappings: list[tuple[str, list[str]]] = [
            ("health", extraction.symptoms),
            ("behaviour", extraction.habits),
            ("health", extraction.sleep_patterns),
            ("health", extraction.hydration_behaviour),
            ("behaviour", extraction.stress_indicators),
            ("communication", extraction.communication_preferences),
            ("health", extraction.health_goals),
        ]

        count = 0
        for category, items in mappings:
            for item in items:
                if item.strip():
                    await self._memory_agent.create_memory(
                        user_id, category, item.strip()
                    )
                    count += 1

        summary_memory = (
            f"[import confidence={extraction.confidence:.2f}] {extraction.summary}"
        )
        await self._memory_agent.create_memory(user_id, "health", summary_memory)
        count += 1
        return count

    async def list_history(self, user_id: int) -> list[ContextImport]:
        return await self._import_repo.list_by_user(user_id)

    @staticmethod
    def parse_stored_extraction(record: ContextImport) -> ContextExtractionResponse | None:
        if not record.extracted_data:
            return None
        try:
            data = json.loads(record.extracted_data)
            return ContextExtractionResponse.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None
