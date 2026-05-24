from datetime import datetime

from pydantic import BaseModel, Field


class ExplanationResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    reasoning: str
    retrieved_memory: list[str] = Field(default_factory=list)
    persona: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime | None = None
