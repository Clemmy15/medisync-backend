"""Unit tests for persona context builder and response mapping."""

from app.models.memory import Memory
from app.models.profile import UserProfile
from app.persona.context_builder import PersonaContextBuilder
from app.persona.engine import PersonaEngine
from app.persona.templates import CANONICAL_PERSONAS


class TestPersonaTemplates:
    def test_canonical_personas_include_examples(self) -> None:
        assert "Sleep-Deprived Student" in CANONICAL_PERSONAS
        assert "Busy Professional" in CANONICAL_PERSONAS
        assert "Fitness Enthusiast" in CANONICAL_PERSONAS
        assert "Budget-Conscious User" in CANONICAL_PERSONAS


class TestPersonaContextBuilder:
    def test_builds_from_profile_and_memory(self) -> None:
        profile = UserProfile(
            user_id=1,
            age_range="18-24",
            occupation="University Student",
            stress_level="high",
            sleep_pattern="5-6 hours",
        )
        memories = [
            Memory(
                id=1, user_id=1, category="behaviour",
                content="Studies late until 2am",
            ),
            Memory(
                id=2, user_id=1, category="health",
                content="Reports headaches",
            ),
        ]
        bundle = PersonaContextBuilder.build(profile, memories, [])

        assert "profile" in bundle.sources_used
        assert "memory" in bundle.sources_used
        assert "behavioural_patterns" in bundle.sources_used
        assert "University Student" in bundle.full_context
        assert bundle.data_richness_score > 0.5

    def test_build_response_maps_reasoning_key(self) -> None:
        response = PersonaEngine._build_response(
            {
                "persona_name": "Fitness Enthusiast",
                "reasoning": "Regular exercise memories detected.",
                "confidence_score": 0.9,
            },
            data_richness=0.8,
        )
        assert response.persona_name == "Fitness Enthusiast"
        assert "exercise" in response.reasoning
        assert response.confidence_score > 0.8
