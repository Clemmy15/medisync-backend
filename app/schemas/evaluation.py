from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.agents import RankingMetrics


class TaskAEvaluationRequest(BaseModel):
    """Review simulation quality evaluation."""

    simulation_id: int | None = None
    expected_rating: int | None = Field(default=None, ge=1, le=5)


class TaskBEvaluationRequest(BaseModel):
    """Recommendation ranking evaluation."""

    batch_id: int | None = None
    relevance_scores: list[float] | None = Field(
        default=None,
        description="Optional ground-truth relevance per ranked item (0-1)",
    )


class TaskAMetrics(BaseModel):
    rating_accuracy: float
    behavioural_fidelity: float
    review_quality_score: float


class TaskBMetrics(RankingMetrics):
    contextual_relevance: float


class EvaluationReportResponse(BaseModel):
    id: int
    task_type: str
    metrics: dict
    report: dict
    created_at: datetime
