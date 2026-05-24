from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import SimulationTargetType
from app.schemas.reasoning import AgentStepsMixin


class ReviewSimulationRequest(BaseModel):
    persona_name: str | None = Field(
        default=None,
        description="Persona to simulate; uses latest if omitted",
    )
    persona_reasoning: str | None = Field(
        default=None,
        description="Optional persona context if not stored in system",
    )
    product_description: str | None = Field(
        default=None,
        max_length=5000,
        description="Healthcare/wellness product being reviewed",
    )
    service_description: str | None = Field(
        default=None,
        max_length=5000,
        description="Healthcare/wellness service being reviewed",
    )
    target_type: SimulationTargetType = Field(
        default=SimulationTargetType.HEALTHCARE_APPS,
        description=(
            "healthcare_apps | wellness_products | telemedicine_services | "
            "pharmacies | fitness_programs"
        ),
    )

    @model_validator(mode="after")
    def require_description(self) -> "ReviewSimulationRequest":
        product = (self.product_description or "").strip()
        service = (self.service_description or "").strip()
        if not product and not service:
            raise ValueError(
                "At least one of product_description or service_description is required"
            )
        self.product_description = product or None
        self.service_description = service or None
        if not self.persona_name and not self.persona_reasoning:
            pass  # engine will use stored persona or raise
        return self


class ReviewSimulationResponse(BaseModel):
    rating: int = Field(ge=1, le=5, examples=[4])
    review: str = Field(description="Simulated review text in persona voice")
    reasoning: str = Field(description="Behavioural reasoning behind rating and tone")
    persona_name: str = ""
    target_type: SimulationTargetType | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rating": 4,
                    "review": (
                        "This sleep app helped me track my late-night habits. "
                        "Reminders are useful though a bit aggressive."
                    ),
                    "reasoning": (
                        "As a Sleep-Deprived Student, practical tools score well; "
                        "minor UX friction prevents a perfect score."
                    ),
                }
            ]
        }
    }


class ReviewSimulationResult(ReviewSimulationResponse, AgentStepsMixin):
    pass


class ReviewSimulationHistoryItem(BaseModel):
    id: int
    user_id: int
    persona_name: str
    target_type: str
    product_description: str | None
    service_description: str | None
    rating: int
    review: str
    reasoning: str
    created_at: datetime

    model_config = {"from_attributes": True}
