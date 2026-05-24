from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import AIPlatform
from app.schemas.reasoning import AgentStepsMixin


class PlatformPromptItem(BaseModel):
    platform: AIPlatform
    prompt: str = Field(description="Copy-paste prompt for the external AI assistant")
    instructions: str = Field(description="Steps to import the response into MedisyncAI")


class PlatformPromptsResponse(BaseModel):
    platforms: list[PlatformPromptItem]


class ImportPromptResponse(BaseModel):
    platform: AIPlatform
    prompt: str
    instructions: str


class ContextAnalyzeRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=10,
        description="Pasted text from ChatGPT, Gemini, or Claude",
        examples=[
            "Symptoms: frequent headaches. Sleep: 5-6 hours on weekdays. Goals: improve sleep."
        ],
    )
    source_platform: AIPlatform | None = Field(
        default=None,
        description="Source AI platform (chatgpt, gemini, claude)",
    )


class FieldConfidenceScores(BaseModel):
    symptoms: float = Field(ge=0.0, le=1.0)
    habits: float = Field(ge=0.0, le=1.0)
    sleep_patterns: float = Field(ge=0.0, le=1.0)
    hydration_behaviour: float = Field(ge=0.0, le=1.0)
    stress_indicators: float = Field(ge=0.0, le=1.0)
    communication_preferences: float = Field(ge=0.0, le=1.0)
    health_goals: float = Field(ge=0.0, le=1.0)


class ContextExtractionResponse(BaseModel):
    """Structured extraction result with per-field and overall confidence."""

    symptoms: list[str] = Field(default_factory=list)
    habits: list[str] = Field(default_factory=list)
    sleep_patterns: list[str] = Field(default_factory=list)
    hydration_behaviour: list[str] = Field(default_factory=list)
    stress_indicators: list[str] = Field(default_factory=list)
    communication_preferences: list[str] = Field(default_factory=list)
    health_goals: list[str] = Field(default_factory=list)
    goals: list[str] = Field(
        default_factory=list,
        description="Alias for health_goals (compact API shape)",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence score",
        examples=[0.92],
    )
    field_confidence: FieldConfidenceScores
    summary: str = Field(description="Brief narrative summary of extracted context")
    source_platform: AIPlatform | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symptoms": ["occasional headaches", "afternoon fatigue"],
                    "habits": ["irregular sleep", "moderate exercise"],
                    "sleep_patterns": ["5-6 hours on weekdays"],
                    "hydration_behaviour": ["2-3 glasses water daily"],
                    "stress_indicators": ["work deadlines", "evening anxiety"],
                    "communication_preferences": ["concise summaries"],
                    "health_goals": ["improve sleep", "reduce stress"],
                    "goals": ["improve sleep", "reduce stress"],
                    "confidence": 0.92,
                    "field_confidence": {
                        "symptoms": 0.88,
                        "habits": 0.85,
                        "sleep_patterns": 0.91,
                        "hydration_behaviour": 0.78,
                        "stress_indicators": 0.87,
                        "communication_preferences": 0.72,
                        "health_goals": 0.9,
                    },
                    "summary": "User shows sleep deprivation and work-related stress.",
                    "source_platform": "chatgpt",
                }
            ]
        }
    }


class ContextSaveRequest(BaseModel):
    content: str = Field(..., min_length=10)
    source_platform: AIPlatform | None = None
    extracted: ContextExtractionResponse | None = Field(
        default=None,
        description="Pre-analyzed extraction; if omitted, server will analyze content",
    )


class ContextAnalyzeResult(ContextExtractionResponse, AgentStepsMixin):
    pass


class ContextSaveResponse(BaseModel):
    id: int
    message: str
    extraction: ContextExtractionResponse
    memories_created: int


class ContextSaveResult(ContextSaveResponse, AgentStepsMixin):
    pass


class ContextImportHistoryItem(BaseModel):
    id: int
    user_id: int
    source_platform: str | None
    confidence: float
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Legacy alias kept for internal use
class ExtractedContext(BaseModel):
    symptoms: list[str] = []
    habits: list[str] = []
    stress_patterns: list[str] = []
    sleep_behaviour: list[str] = []
    hydration_habits: list[str] = []
    lifestyle_concerns: list[str] = []
    communication_preferences: list[str] = []
    health_goals: list[str] = []

    @field_validator(
        "symptoms", "habits", "stress_patterns", "sleep_behaviour",
        "hydration_habits", "lifestyle_concerns", "communication_preferences",
        "health_goals",
        mode="before",
    )
    @classmethod
    def coerce_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]
