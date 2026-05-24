import logging
from typing import Any

from app.context_import.confidence import build_field_confidence, compute_overall_confidence
from app.domain.enums import AIPlatform
from app.schemas.context_import import ContextExtractionResponse, FieldConfidenceScores
from app.services.llm_service import LLMService
from app.utils.prompts import CONTEXT_EXTRACTION_SYSTEM

logger = logging.getLogger(__name__)


def _as_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalize_llm_result(result: dict[str, Any]) -> dict[str, list[str]]:
    """Map LLM output keys (including legacy names) to canonical field names."""
    sleep = result.get("sleep_patterns") or result.get("sleep_behaviour") or []
    hydration = result.get("hydration_behaviour") or result.get("hydration_habits") or []
    stress = result.get("stress_indicators") or result.get("stress_patterns") or []
    goals = result.get("health_goals") or result.get("goals") or []

    return {
        "symptoms": _as_str_list(result.get("symptoms")),
        "habits": _as_str_list(result.get("habits")),
        "sleep_patterns": _as_str_list(sleep),
        "hydration_behaviour": _as_str_list(hydration),
        "stress_indicators": _as_str_list(stress),
        "communication_preferences": _as_str_list(
            result.get("communication_preferences")
        ),
        "health_goals": _as_str_list(goals),
    }


class ContextExtractor:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    async def extract(
        self,
        content: str,
        source_platform: AIPlatform | None = None,
    ) -> ContextExtractionResponse:
        platform_hint = (
            f"\nSource platform: {source_platform.value}" if source_platform else ""
        )
        result = await self._llm.complete_json(
            CONTEXT_EXTRACTION_SYSTEM,
            f"Extract health context from:{platform_hint}\n\n{content}",
        )

        normalized = _normalize_llm_result(result)
        llm_field_scores = result.get("field_confidence") or result.get(
            "confidence_scores"
        )
        if isinstance(llm_field_scores, dict):
            llm_field_scores = {str(k): v for k, v in llm_field_scores.items()}
        else:
            llm_field_scores = None

        field_confidence = build_field_confidence(
            normalized, content, llm_field_scores
        )
        overall = compute_overall_confidence(
            field_confidence,
            result.get("confidence") or result.get("confidence_score"),
        )

        goals = normalized["health_goals"]
        logger.info(
            "Extracted context: %d fields, confidence=%.2f",
            sum(1 for v in normalized.values() if v),
            overall,
        )

        return ContextExtractionResponse(
            symptoms=normalized["symptoms"],
            habits=normalized["habits"],
            sleep_patterns=normalized["sleep_patterns"],
            hydration_behaviour=normalized["hydration_behaviour"],
            stress_indicators=normalized["stress_indicators"],
            communication_preferences=normalized["communication_preferences"],
            health_goals=goals,
            goals=goals,
            confidence=overall,
            field_confidence=field_confidence,
            summary=str(result.get("summary", "Context analyzed successfully.")),
            source_platform=source_platform,
        )
