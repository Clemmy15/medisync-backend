"""Analytics engine — aggregated metrics and chart-ready time series."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.time_series import (
    cumulative_series,
    last_n_day_labels,
    merge_daily_counts,
)
from app.models.analytics_event import AnalyticsEvent
from app.models.context_import import ContextImport
from app.models.memory import Memory
from app.models.persona import Persona
from app.models.recommendation import Recommendation
from app.models.review_simulation import ReviewSimulation
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    CategoryCount,
    ChartData,
    ChartDataset,
    OverviewMetrics,
    PersonaAnalyticsResponse,
    PersonaDistributionItem,
    RecommendationAnalytics,
)

logger = logging.getLogger(__name__)

CHART_DAYS = 14
ACTIVE_USER_DAYS = 30


class AnalyticsEngine:
    async def get_overview(self, db: AsyncSession) -> AnalyticsOverview:
        labels = last_n_day_labels(CHART_DAYS)
        start = datetime.now(timezone.utc) - timedelta(days=CHART_DAYS - 1)
        active_cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVE_USER_DAYS)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        metrics = OverviewMetrics(
            active_users=await self._count_active_users(db, active_cutoff),
            total_users=await db.scalar(select(func.count()).select_from(User)) or 0,
            contexts_imported=await db.scalar(
                select(func.count()).select_from(ContextImport)
            )
            or 0,
            recommendations_generated=await db.scalar(
                select(func.count()).select_from(Recommendation)
            )
            or 0,
            reviews_simulated=await db.scalar(
                select(func.count()).select_from(ReviewSimulation)
            )
            or 0,
            personas_generated=await db.scalar(
                select(func.count()).select_from(Persona)
            )
            or 0,
            total_memories=await db.scalar(select(func.count()).select_from(Memory)) or 0,
            memories_added_7d=await db.scalar(
                select(func.count())
                .select_from(Memory)
                .where(Memory.created_at >= seven_days_ago)
            )
            or 0,
        )

        rec_daily = await self._daily_counts(db, Recommendation, start)
        review_daily = await self._daily_counts(db, ReviewSimulation, start)
        import_daily = await self._daily_counts(db, ContextImport, start)
        memory_daily = await self._daily_counts(db, Memory, start)

        activity_chart = ChartData(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Recommendations",
                    data=merge_daily_counts(labels, rec_daily),
                ),
                ChartDataset(
                    label="Reviews simulated",
                    data=merge_daily_counts(labels, review_daily),
                ),
                ChartDataset(
                    label="Contexts imported",
                    data=merge_daily_counts(labels, import_daily),
                ),
            ],
        )

        daily_new = merge_daily_counts(labels, memory_daily)
        memory_growth_chart = ChartData(
            labels=labels,
            datasets=[
                ChartDataset(label="New memories", data=daily_new),
                ChartDataset(
                    label="Cumulative memories",
                    data=cumulative_series(daily_new),
                ),
            ],
        )

        logger.debug("Built analytics overview for %d total users", metrics.total_users)
        return AnalyticsOverview(
            metrics=metrics,
            activity_chart=activity_chart,
            memory_growth_chart=memory_growth_chart,
        )

    async def get_persona_distribution(
        self, db: AsyncSession
    ) -> PersonaAnalyticsResponse:
        result = await db.execute(
            select(Persona.persona_name, func.count(Persona.id))
            .group_by(Persona.persona_name)
            .order_by(func.count(Persona.id).desc())
        )
        rows = result.all()
        total = sum(row[1] for row in rows)

        distribution = [
            PersonaDistributionItem(
                persona_name=row[0],
                count=row[1],
                percentage=round(100.0 * row[1] / total, 1) if total else 0.0,
            )
            for row in rows
        ]

        chart = ChartData(
            labels=[item.persona_name for item in distribution],
            datasets=[
                ChartDataset(
                    label="Persona assignments",
                    data=[item.count for item in distribution],
                )
            ],
        )

        return PersonaAnalyticsResponse(
            total_personas=total,
            unique_persona_types=len(distribution),
            distribution=distribution,
            chart=chart,
        )

    async def get_recommendation_analytics(
        self, db: AsyncSession
    ) -> RecommendationAnalytics:
        labels = last_n_day_labels(CHART_DAYS)
        start = datetime.now(timezone.utc) - timedelta(days=CHART_DAYS - 1)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        total = await db.scalar(select(func.count()).select_from(Recommendation)) or 0
        avg_conf = await db.scalar(select(func.avg(Recommendation.confidence))) or 0.0
        recent_7d = (
            await db.scalar(
                select(func.count())
                .select_from(Recommendation)
                .where(Recommendation.created_at >= seven_days_ago)
            )
            or 0
        )

        cat_result = await db.execute(
            select(Recommendation.category, func.count(Recommendation.id))
            .group_by(Recommendation.category)
            .order_by(func.count(Recommendation.id).desc())
        )
        cat_rows = cat_result.all()
        cat_total = sum(row[1] for row in cat_rows) or 1

        by_category = [
            CategoryCount(
                category=row[0],
                count=row[1],
                percentage=round(100.0 * row[1] / cat_total, 1),
            )
            for row in cat_rows
        ]

        category_chart = ChartData(
            labels=[item.category for item in by_category],
            datasets=[
                ChartDataset(
                    label="Recommendations",
                    data=[item.count for item in by_category],
                )
            ],
        )

        rec_daily = await self._daily_counts(db, Recommendation, start)
        daily_chart = ChartData(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Recommendations generated",
                    data=merge_daily_counts(labels, rec_daily),
                )
            ],
        )

        return RecommendationAnalytics(
            total=total,
            average_confidence=round(float(avg_conf), 3),
            recent_count_7d=recent_7d,
            by_category=by_category,
            category_chart=category_chart,
            daily_chart=daily_chart,
        )

    @staticmethod
    async def _count_active_users(db: AsyncSession, since: datetime) -> int:
        from_events = await db.scalar(
            select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
                AnalyticsEvent.user_id.isnot(None),
                AnalyticsEvent.created_at >= since,
            )
        )
        if from_events:
            return from_events

        # Fallback: users with any recorded activity in core tables
        subqueries_users: set[int] = set()
        for model in (Recommendation, ContextImport, ReviewSimulation, Persona, Memory):
            result = await db.execute(
                select(func.distinct(model.user_id)).where(model.created_at >= since)
            )
            subqueries_users.update(row[0] for row in result.all())
        return len(subqueries_users)

    @staticmethod
    async def _daily_counts(
        db: AsyncSession,
        model: type,
        since: datetime,
    ) -> list[tuple[str | None, int]]:
        day_col = func.date(model.created_at)
        result = await db.execute(
            select(day_col, func.count())
            .where(model.created_at >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
        return [(str(row[0]) if row[0] is not None else None, row[1]) for row in result.all()]
