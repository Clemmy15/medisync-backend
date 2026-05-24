from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import RecommendationCategory
from app.schemas.reasoning import AgentStepsMixin


class RecommendationGenerateRequest(BaseModel):
    category: RecommendationCategory | None = Field(
        default=None,
        description=(
            "Target category: health_apps, wellness_plans, productivity_wellness, "
            "sleep_improvement, hydration_improvement, stress_reduction"
        ),
    )


class RecommendationResponse(BaseModel):
    category: RecommendationCategory
    recommendation: str = Field(description="Personalized actionable recommendation")
    reasoning: str = Field(description="Why this recommendation fits the user")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "sleep_improvement",
                    "recommendation": (
                        "Use a consistent 10:30 PM wind-down routine with screen-free "
                        "30 minutes and a sleep tracking app to reach 7-8 hours nightly."
                    ),
                    "reasoning": (
                        "As a Sleep-Deprived Student with 5-6h sleep and exam stress, "
                        "structured bedtime habits address the primary health gap."
                    ),
                    "confidence": 0.88,
                }
            ]
        }
    }


class RecommendationResult(RecommendationResponse, AgentStepsMixin):
    pass


class RecommendationHistoryItem(BaseModel):
    id: int
    user_id: int
    category: str
    recommendation: str
    reasoning: str
    confidence: float
    sources_used: list[str] = Field(default_factory=list)
    is_saved: bool = False
    marked_helpful: bool | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, rec: object) -> "RecommendationHistoryItem":
        import json

        sources: list[str] = []
        raw = getattr(rec, "sources_used", None)
        if raw:
            try:
                sources = json.loads(raw)
            except json.JSONDecodeError:
                sources = []
        return cls(
            id=rec.id,
            user_id=rec.user_id,
            category=rec.category,
            recommendation=rec.recommendation,
            reasoning=rec.reasoning,
            confidence=rec.confidence,
            sources_used=sources,
            is_saved=bool(getattr(rec, "is_saved", False)),
            marked_helpful=getattr(rec, "marked_helpful", None),
            created_at=rec.created_at,
        )


class RecommendationSaveResponse(BaseModel):
    id: int
    is_saved: bool = True
    memory_created: bool = False
    message: str = "Recommendation saved"


class RecommendationHelpfulResponse(BaseModel):
    id: int
    marked_helpful: bool = True
    message: str = "Thanks for your feedback"
