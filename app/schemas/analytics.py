from pydantic import BaseModel, Field


class ChartDataset(BaseModel):
    """Single series for bar/line/doughnut charts (Chart.js, Recharts, etc.)."""

    label: str
    data: list[int | float]


class ChartData(BaseModel):
    """Chart-ready payload: labels on X-axis, one or more datasets."""

    labels: list[str] = Field(description="X-axis labels (e.g. dates or categories)")
    datasets: list[ChartDataset]


class OverviewMetrics(BaseModel):
    active_users: int = Field(description="Distinct users with activity in last 30 days")
    total_users: int
    contexts_imported: int
    recommendations_generated: int
    reviews_simulated: int
    personas_generated: int
    total_memories: int
    memories_added_7d: int = Field(description="New memories in the last 7 days")


class AnalyticsOverview(BaseModel):
    metrics: OverviewMetrics
    activity_chart: ChartData = Field(
        description="Daily recommendations, reviews, and context imports (14 days)"
    )
    memory_growth_chart: ChartData = Field(
        description="Daily new memories and cumulative total (14 days)"
    )


class PersonaDistributionItem(BaseModel):
    persona_name: str
    count: int
    percentage: float = Field(ge=0.0, le=100.0)


class PersonaAnalyticsResponse(BaseModel):
    total_personas: int
    unique_persona_types: int
    distribution: list[PersonaDistributionItem]
    chart: ChartData


# Backward-compatible alias
PersonaDistribution = PersonaDistributionItem


class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float = Field(ge=0.0, le=100.0)


class RecommendationAnalytics(BaseModel):
    total: int
    average_confidence: float
    recent_count_7d: int
    by_category: list[CategoryCount]
    category_chart: ChartData
    daily_chart: ChartData = Field(description="Recommendations per day (last 14 days)")
