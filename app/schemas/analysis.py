from pydantic import BaseModel

from app.domain.enums import RiskLevel
from app.schemas.reasoning import AgentStepsMixin
from app.schemas.risk_detection import (
    RiskDetectionRequest,
    RiskDetectionResponse,
    RiskDetectionResult,
)

# Backward-compatible aliases
RiskAnalysisRequest = RiskDetectionRequest
RiskAnalysisResponse = RiskDetectionResponse
RiskAnalysisResult = RiskDetectionResult


class BehaviourAnalysisResponse(BaseModel):
    trend_analysis: str
    behavioural_insights: list[str]
    confidence_scores: dict[str, float]


class BehaviourAnalysisResult(BehaviourAnalysisResponse, AgentStepsMixin):
    pass


__all__ = [
    "BehaviourAnalysisResponse",
    "BehaviourAnalysisResult",
    "RiskAnalysisRequest",
    "RiskAnalysisResponse",
    "RiskAnalysisResult",
    "RiskDetectionRequest",
    "RiskDetectionResponse",
    "RiskDetectionResult",
    "RiskLevel",
]
