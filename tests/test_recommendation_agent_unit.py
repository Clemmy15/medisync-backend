"""Unit tests for Recommendation Agent context and response building."""

from app.domain.enums import RecommendationCategory
from app.models.memory import Memory
from app.models.persona import Persona
from app.models.profile import UserProfile
from app.recommendations.context_builder import RecommendationContextBuilder
from app.recommendations.engine import RecommendationEngine


class TestRecommendationContextBuilder:
    def test_builds_all_sources(self) -> None:
        profile = UserProfile(
            user_id=1,
            occupation="Developer",
            sleep_pattern="6 hours",
        )
        persona = Persona(
            user_id=1,
            persona_name="Busy Professional",
            persona_reasoning="High work stress",
            confidence_score=0.85,
        )
        memories = [
            Memory(id=1, user_id=1, category="health", content="Afternoon fatigue"),
        ]
        bundle = RecommendationContextBuilder.build(
            profile,
            persona,
            memories,
            [],
            RecommendationCategory.SLEEP_IMPROVEMENT,
        )

        assert "profile" in bundle.sources_used
        assert "persona" in bundle.sources_used
        assert "memory" in bundle.sources_used
        assert "sleep_improvement" in bundle.full_context

    def test_category_focus_included(self) -> None:
        bundle = RecommendationContextBuilder.build(
            None, None, [], [], RecommendationCategory.HYDRATION_IMPROVEMENT
        )
        assert "hydration" in bundle.category_focus.lower()


class TestRecommendationResponse:
    def test_build_response_with_category(self) -> None:
        response = RecommendationEngine._build_response(
            {
                "category": "wellness_plans",
                "recommendation": "Try a 4-week wellness plan.",
                "reasoning": "Holistic approach fits multiple goals.",
                "confidence": 0.9,
            },
            data_richness=0.8,
            requested_category=None,
        )
        assert response.category == RecommendationCategory.WELLNESS_PLANS
        assert response.confidence > 0.7
