from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.analytics import ChartData


class PersonaCard(BaseModel):
    persona_name: str | None = None
    reasoning: str | None = None
    confidence_score: float | None = None


class HealthSummaryCard(BaseModel):
    age_range: str | None = None
    occupation: str | None = None
    activity_level: str | None = None
    sleep_pattern: str | None = None
    stress_level: str | None = None
    hydration_level: str | None = None
    dietary_preferences: str | None = None
    health_goals: str | None = None


class RiskLevelCard(BaseModel):
    risk_level: str | None = None
    reasoning: str | None = None
    recommended_action: str | None = None


class RecentActivityItem(BaseModel):
    activity_type: str
    title: str
    description: str
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    persona: PersonaCard
    health_summary: HealthSummaryCard
    risk: RiskLevelCard
    recommendation_count: int = 0
    recent_activity: list[RecentActivityItem] = Field(default_factory=list)
    sleep_trend_chart: ChartData
    stress_trend_chart: ChartData
    recommendation_activity_chart: ChartData
