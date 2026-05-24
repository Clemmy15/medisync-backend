"""Unit tests for context import extraction and confidence scoring."""

import pytest

from app.context_import.confidence import (
    build_field_confidence,
    compute_overall_confidence,
    score_field_named,
)
from app.context_import.extractor import ContextExtractor, _normalize_llm_result
from app.context_import.prompts import (
    PLATFORM_IMPORT_PROMPTS,
    get_all_platform_prompts,
    get_import_prompt,
)
from app.domain.enums import AIPlatform
from app.schemas.context_import import FieldConfidenceScores
from app.services.llm_service import LLMService


class TestPlatformPrompts:
    def test_all_platforms_have_prompts(self) -> None:
        prompts = get_all_platform_prompts()
        assert set(prompts.keys()) == {
            AIPlatform.CHATGPT,
            AIPlatform.GEMINI,
            AIPlatform.CLAUDE,
        }

    def test_chatgpt_prompt_contains_categories(self) -> None:
        prompt = get_import_prompt(AIPlatform.CHATGPT)
        assert "Symptoms" in prompt or "symptoms" in prompt.lower()
        assert "Sleep" in prompt or "sleep" in prompt.lower()
        assert "goals" in prompt.lower()

    @pytest.mark.parametrize("platform", list(AIPlatform))
    def test_each_platform_prompt_unique(self, platform: AIPlatform) -> None:
        assert platform in PLATFORM_IMPORT_PROMPTS
        assert len(PLATFORM_IMPORT_PROMPTS[platform]) > 100


class TestNormalizeLlmResult:
    def test_maps_legacy_keys(self) -> None:
        raw = {
            "symptoms": ["headache"],
            "sleep_behaviour": ["6 hours"],
            "stress_patterns": ["work stress"],
            "hydration_habits": ["low water"],
            "health_goals": ["sleep more"],
        }
        normalized = _normalize_llm_result(raw)
        assert normalized["symptoms"] == ["headache"]
        assert normalized["sleep_patterns"] == ["6 hours"]
        assert normalized["stress_indicators"] == ["work stress"]
        assert normalized["hydration_behaviour"] == ["low water"]
        assert normalized["health_goals"] == ["sleep more"]


class TestConfidenceScoring:
    def test_empty_items_zero_confidence(self) -> None:
        assert score_field_named("symptoms", [], "some text") == 0.0

    def test_items_increase_confidence(self) -> None:
        score = score_field_named(
            "symptoms",
            ["frequent headaches", "afternoon fatigue"],
            "I have frequent headaches and afternoon fatigue daily",
        )
        assert 0.4 < score <= 0.99

    def test_overall_confidence_with_llm(self) -> None:
        fields = FieldConfidenceScores(
            symptoms=0.9,
            habits=0.8,
            sleep_patterns=0.85,
            hydration_behaviour=0.7,
            stress_indicators=0.88,
            communication_preferences=0.75,
            health_goals=0.92,
        )
        overall = compute_overall_confidence(fields, llm_overall=0.92)
        assert 0.8 <= overall <= 0.99

    def test_build_field_confidence_from_extracted(self) -> None:
        extracted = {
            "symptoms": ["headache"],
            "habits": [],
            "sleep_patterns": ["5 hours"],
            "hydration_behaviour": [],
            "stress_indicators": ["anxiety"],
            "communication_preferences": [],
            "health_goals": ["better sleep"],
        }
        scores = build_field_confidence(
            extracted,
            "headache sleep anxiety goals",
            {"symptoms": 0.95},
        )
        assert scores.symptoms >= 0.9
        assert scores.habits == 0.0


@pytest.mark.asyncio
class TestContextExtractor:
    async def test_extract_returns_confidence(self) -> None:
        extractor = ContextExtractor(LLMService())
        content = (
            "Symptoms: headaches and fatigue. "
            "Sleep: 5-6 hours. Goals: improve sleep and reduce stress."
        )
        result = await extractor.extract(content, AIPlatform.CHATGPT)

        assert len(result.symptoms) >= 1
        assert len(result.habits) >= 1
        assert result.goals == result.health_goals
        assert 0.0 < result.confidence <= 1.0
        assert 0.0 <= result.field_confidence.symptoms <= 1.0
        assert result.summary
