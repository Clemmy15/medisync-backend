from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import RiskLevel
from app.schemas.reasoning import AgentStepsMixin


class RiskDetectionRequest(BaseModel):
    symptoms: list[str] = Field(
        default_factory=list,
        description="Current or reported symptoms to evaluate",
        examples=[["persistent headache", "chest tightness", "fatigue"]],
    )
    context: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional additional health context",
    )


class RiskDetectionResponse(BaseModel):
    risk_level: RiskLevel = Field(
        description="low | moderate | high (Low, Moderate, High)",
        examples=["moderate"],
    )
    reasoning: str = Field(
        description="Explanation covering symptom patterns, deterioration, and recurring concerns"
    )
    recommended_action: str = Field(
        description="Actionable next step appropriate to the risk level"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "risk_level": "moderate",
                    "reasoning": (
                        "Recurring headaches and fatigue across memory entries suggest "
                        "a worsening pattern; no immediate emergency indicators."
                    ),
                    "recommended_action": (
                        "Schedule a primary care visit within 2 weeks; "
                        "track symptoms daily."
                    ),
                }
            ]
        }
    }


class RiskDetectionResult(RiskDetectionResponse, AgentStepsMixin):
    pass


class RiskAssessmentHistoryItem(BaseModel):
    id: int
    user_id: int
    risk_level: str
    reasoning: str
    recommended_action: str
    reported_symptoms: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, record: object) -> "RiskAssessmentHistoryItem":
        import json

        symptoms: list[str] = []
        raw = getattr(record, "reported_symptoms", None)
        if raw:
            try:
                symptoms = json.loads(raw)
            except json.JSONDecodeError:
                symptoms = []
        return cls(
            id=record.id,
            user_id=record.user_id,
            risk_level=record.risk_level,
            reasoning=record.reasoning,
            recommended_action=record.recommended_action,
            reported_symptoms=symptoms,
            created_at=record.created_at,
        )
