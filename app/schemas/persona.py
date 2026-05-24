from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.reasoning import AgentStepsMixin


class PersonaGenerateResponse(BaseModel):
    """Generated behavioural persona."""

    persona_name: str = Field(
        examples=["Sleep-Deprived Student", "Busy Professional", "Fitness Enthusiast"]
    )
    reasoning: str = Field(
        description="Explanation of why this persona was assigned"
    )
    confidence_score: float = Field(ge=0.0, le=1.0, examples=[0.85])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "persona_name": "Sleep-Deprived Student",
                    "reasoning": (
                        "Profile shows university occupation with 5-6h sleep and "
                        "memories indicate late-night study habits."
                    ),
                    "confidence_score": 0.87,
                }
            ]
        }
    }


class PersonaGenerateResult(PersonaGenerateResponse, AgentStepsMixin):
    pass


class PersonaHistoryItem(BaseModel):
    id: int
    user_id: int
    persona_name: str
    reasoning: str
    confidence_score: float
    sources_used: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_persona(cls, persona: object) -> "PersonaHistoryItem":
        import json

        sources: list[str] = []
        raw = getattr(persona, "sources_used", None)
        if raw:
            try:
                sources = json.loads(raw)
            except json.JSONDecodeError:
                sources = []
        return cls(
            id=persona.id,
            user_id=persona.user_id,
            persona_name=persona.persona_name,
            reasoning=persona.persona_reasoning,
            confidence_score=persona.confidence_score,
            sources_used=sources,
            created_at=persona.created_at,
        )


class PersonaResponse(BaseModel):
    """Alias for latest/current persona."""

    id: int
    user_id: int
    persona_name: str
    reasoning: str
    confidence_score: float
    sources_used: list[str] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_orm_persona(cls, persona: object) -> "PersonaResponse":
        item = PersonaHistoryItem.from_orm_persona(persona)
        return cls(**item.model_dump())
