"""Unit tests for Review Simulation context builder."""

from app.domain.enums import SimulationTargetType
from app.models.persona import Persona
from app.review_simulation.context_builder import ReviewSimulationContextBuilder
from app.review_simulation.engine import ReviewSimulationEngine


class TestReviewSimulationContext:
    def test_builds_product_and_service(self) -> None:
        persona = Persona(
            user_id=1,
            persona_name="Busy Professional",
            persona_reasoning="Works long hours, values efficiency",
            confidence_score=0.85,
        )
        ctx = ReviewSimulationContextBuilder.build(
            persona=persona,
            persona_name="",
            persona_reasoning="",
            product_description="Wellness vitamin pack",
            service_description="Corporate health coaching",
            target_type=SimulationTargetType.WELLNESS_PRODUCTS,
        )
        assert "Busy Professional" in ctx.llm_prompt
        assert "Wellness vitamin" in ctx.llm_prompt
        assert "health coaching" in ctx.llm_prompt
        assert "wellness_products" in ctx.llm_prompt

    def test_build_response_clamps_rating(self) -> None:
        response = ReviewSimulationEngine._build_response(
            {"rating": 10, "review": "Great", "reasoning": "Because"},
            persona_name="Test",
            target_type=SimulationTargetType.PHARMACIES,
        )
        assert response.rating == 5
