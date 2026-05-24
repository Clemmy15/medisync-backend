from dataclasses import dataclass

from app.domain.enums import SimulationTargetType
from app.models.persona import Persona
from app.review_simulation.targets import TARGET_SIMULATION_HINTS, get_target_label


@dataclass
class ReviewSimulationContext:
    persona_name: str
    persona_reasoning: str
    product_description: str | None
    service_description: str | None
    target_type: SimulationTargetType
    target_label: str
    simulation_hints: str

    @property
    def llm_prompt(self) -> str:
        lines = [
            f"=== USER PERSONA ===",
            f"Name: {self.persona_name}",
            f"Behavioural profile: {self.persona_reasoning}",
            "",
            f"=== TARGET TYPE ===",
            f"{self.target_label} ({self.target_type.value})",
            f"Simulation guidance: {self.simulation_hints}",
        ]
        if self.product_description:
            lines.extend(["", "=== PRODUCT DESCRIPTION ===", self.product_description])
        if self.service_description:
            lines.extend(["", "=== SERVICE DESCRIPTION ===", self.service_description])
        lines.extend([
            "",
            "Simulate how this persona would realistically rate and review the "
            "product/service. Use authentic language matching their communication style.",
        ])
        return "\n".join(lines)


class ReviewSimulationContextBuilder:
    @staticmethod
    def build(
        persona: Persona | None,
        persona_name: str,
        persona_reasoning: str,
        product_description: str | None,
        service_description: str | None,
        target_type: SimulationTargetType,
    ) -> ReviewSimulationContext:
        name = persona.persona_name if persona else persona_name
        reasoning = persona.persona_reasoning if persona else persona_reasoning

        return ReviewSimulationContext(
            persona_name=name,
            persona_reasoning=reasoning,
            product_description=product_description,
            service_description=service_description,
            target_type=target_type,
            target_label=get_target_label(target_type),
            simulation_hints=TARGET_SIMULATION_HINTS[target_type],
        )
