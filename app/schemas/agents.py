from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import RecommendationCategory
from app.schemas.reasoning import AgentStepsMixin


class ColdStartRequest(BaseModel):
    """Uses onboarding profile when body empty; optional overrides."""

    occupation: str | None = None
    health_goals: str | None = None
    age_range: str | None = None
    activity_level: str | None = None
    stress_level: str | None = None
    sleep_pattern: str | None = None


class ColdStartRecommendationItem(BaseModel):
    category: RecommendationCategory
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)


class ColdStartResponse(BaseModel):
    persona: str
    recommendations: list[ColdStartRecommendationItem]
    reasoning: str
    cold_start_id: int | None = None


class ColdStartResult(ColdStartResponse, AgentStepsMixin):
    pass


class CrossDomainRankRequest(BaseModel):
    concern: str = Field(
        ...,
        min_length=3,
        examples=["Poor sleep and fatigue"],
    )


class RankedRecommendationItem(BaseModel):
    rank: int = Field(ge=1)
    category: RecommendationCategory
    recommendation: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class RankingMetrics(BaseModel):
    ndcg_at_10: float
    hit_rate: float
    recommendation_diversity: float
    item_count: int


class CrossDomainRankResponse(BaseModel):
    concern: str
    ranked_recommendations: list[RankedRecommendationItem]
    ranking_metrics: RankingMetrics
    batch_id: int | None = None


class CrossDomainRankResult(CrossDomainRankResponse, AgentStepsMixin):
    pass


class NigerianContextResponse(BaseModel):
    affordability_tier: str
    affordability_notes: str
    lifestyle_patterns: str
    communication_style: str
    contextual_reasoning: str
    record_id: int | None = None


class FidelityEvidenceItem(BaseModel):
    factor: str
    score: float = Field(ge=0.0, le=1.0)
    note: str


class FidelityReport(BaseModel):
    fidelity_score: float = Field(ge=0.0, le=1.0)
    evidence: list[FidelityEvidenceItem]


class OrchestrationRequest(BaseModel):
    concern: str | None = Field(
        default=None,
        description="Health concern for cross-domain ranking (e.g. poor sleep)",
    )
    run_cold_start: bool = Field(
        default=False,
        description="Force cold-start path when user has little history",
    )


class OrchestrationStep(BaseModel):
    step: str
    status: str
    detail: str | None = None


class OrchestrationResponse(BaseModel):
    run_id: int
    status: str
    pipeline: list[OrchestrationStep]
    persona_name: str | None = None
    ranking_batch_id: int | None = None
    explanation_id: int | None = None
    summary: str


class OrchestrationResult(OrchestrationResponse, AgentStepsMixin):
    pass
