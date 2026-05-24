"""User dashboard overview — cards, activity feed, and wellness trend charts."""

import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.time_series import last_n_day_labels, merge_daily_counts
from app.models.context_import import ContextImport
from app.models.memory import Memory
from app.models.persona import Persona
from app.models.recommendation import Recommendation
from app.models.review_simulation import ReviewSimulation
from app.models.risk_assessment import RiskAssessment
from app.repositories.profile_repository import ProfileRepository
from app.risk_detection.engine import RiskDetectionEngine
from app.persona.engine import PersonaEngine
from app.recommendations.engine import RecommendationEngine
from app.schemas.analytics import ChartData, ChartDataset
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    HealthSummaryCard,
    PersonaCard,
    RecentActivityItem,
    RiskLevelCard,
)

logger = logging.getLogger(__name__)

CHART_DAYS = 14

SLEEP_KEYWORDS = re.compile(
    r"\b(sleep|insomnia|rested|fatigue|tired|nap|bedtime|wake)\b", re.I
)
STRESS_KEYWORDS = re.compile(
    r"\b(stress|stressed|anxious|anxiety|overwhelm|burnout|pressure)\b", re.I
)

RISK_SCORES = {"low": 25, "moderate": 55, "high": 80}


class DashboardEngine:
    def __init__(
        self,
        persona_engine: PersonaEngine,
        risk_engine: RiskDetectionEngine,
        recommendation_engine: RecommendationEngine,
    ) -> None:
        self._persona = persona_engine
        self._risk = risk_engine
        self._recommendations = recommendation_engine

    async def get_overview(
        self, db: AsyncSession, user_id: int
    ) -> DashboardOverviewResponse:
        labels = last_n_day_labels(CHART_DAYS)
        start = datetime.now(timezone.utc) - timedelta(days=CHART_DAYS - 1)

        profile = await ProfileRepository(db).get_by_user_id(user_id)
        health = HealthSummaryCard(
            age_range=profile.age_range if profile else None,
            occupation=profile.occupation if profile else None,
            activity_level=profile.activity_level if profile else None,
            sleep_pattern=profile.sleep_pattern if profile else None,
            stress_level=profile.stress_level if profile else None,
            hydration_level=profile.hydration_level if profile else None,
            dietary_preferences=profile.dietary_preferences if profile else None,
            health_goals=profile.health_goals if profile else None,
        )

        persona_rec = await self._persona.get_current(user_id)
        persona = PersonaCard(
            persona_name=persona_rec.persona_name if persona_rec else None,
            reasoning=persona_rec.reasoning if persona_rec else None,
            confidence_score=persona_rec.confidence_score if persona_rec else None,
        )

        risk_rec = await self._risk.get_current(user_id)
        risk = RiskLevelCard(
            risk_level=risk_rec.risk_level if risk_rec else None,
            reasoning=risk_rec.reasoning if risk_rec else None,
            recommended_action=risk_rec.recommended_action if risk_rec else None,
        )

        rec_count = (
            await db.scalar(
                select(func.count())
                .select_from(Recommendation)
                .where(Recommendation.user_id == user_id)
            )
            or 0
        )

        sleep_baseline = _profile_sleep_score(health.sleep_pattern)
        stress_baseline = _profile_stress_score(health.stress_level)

        memories = await self._user_memories_since(db, user_id, start)
        sleep_daily = _keyword_daily_scores(labels, memories, SLEEP_KEYWORDS, sleep_baseline, boost=8)
        stress_daily = await self._stress_daily_series(
            db, user_id, labels, start, memories, stress_baseline
        )

        rec_daily = await self._user_daily_counts(
            db, Recommendation, user_id, start
        )

        recent = await self._build_recent_activity(db, user_id)

        return DashboardOverviewResponse(
            persona=persona,
            health_summary=health,
            risk=risk,
            recommendation_count=rec_count,
            recent_activity=recent,
            sleep_trend_chart=ChartData(
                labels=labels,
                datasets=[
                    ChartDataset(label="Sleep wellness index", data=sleep_daily)
                ],
            ),
            stress_trend_chart=ChartData(
                labels=labels,
                datasets=[
                    ChartDataset(label="Stress index", data=stress_daily)
                ],
            ),
            recommendation_activity_chart=ChartData(
                labels=labels,
                datasets=[
                    ChartDataset(
                        label="Recommendations",
                        data=merge_daily_counts(labels, rec_daily),
                    )
                ],
            ),
        )

    async def _user_daily_counts(
        self,
        db: AsyncSession,
        model: type,
        user_id: int,
        since: datetime,
    ) -> list[tuple[str | None, int]]:
        day_col = func.date(model.created_at)
        result = await db.execute(
            select(day_col, func.count())
            .where(model.user_id == user_id, model.created_at >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
        return [(str(row[0]) if row[0] is not None else None, row[1]) for row in result.all()]

    @staticmethod
    async def _user_memories_since(
        db: AsyncSession, user_id: int, since: datetime
    ) -> list[Memory]:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id, Memory.created_at >= since)
            .order_by(Memory.created_at.asc())
        )
        return list(result.scalars().all())

    async def _stress_daily_series(
        self,
        db: AsyncSession,
        user_id: int,
        labels: list[str],
        start: datetime,
        memories: list[Memory],
        baseline: int,
    ) -> list[int]:
        day_col = func.date(RiskAssessment.created_at)
        result = await db.execute(
            select(day_col, RiskAssessment.risk_level)
            .where(
                RiskAssessment.user_id == user_id,
                RiskAssessment.created_at >= start,
            )
            .order_by(RiskAssessment.created_at.asc())
        )
        risk_by_day: dict[str, int] = {}
        for day, level in result.all():
            if day is None:
                continue
            key = str(day)
            risk_by_day[key] = RISK_SCORES.get((level or "").lower(), baseline)

        stress_memory_boost = _keyword_daily_scores(
            labels, memories, STRESS_KEYWORDS, 0, boost=10
        )

        series: list[int] = []
        for i, label in enumerate(labels):
            if label in risk_by_day:
                score = risk_by_day[label]
            else:
                score = min(100, baseline + stress_memory_boost[i])
            series.append(min(100, max(0, score)))
        return series

    async def _build_recent_activity(
        self, db: AsyncSession, user_id: int
    ) -> list[RecentActivityItem]:
        items: list[RecentActivityItem] = []

        recs = await self._recommendations.get_history(user_id, limit=5)
        for r in recs:
            items.append(
                RecentActivityItem(
                    activity_type="recommendation",
                    title=f"Recommendation · {r.category.replace('_', ' ')}",
                    description=_truncate(r.recommendation, 120),
                    created_at=r.created_at,
                )
            )

        mem_result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.created_at.desc())
            .limit(5)
        )
        for m in mem_result.scalars().all():
            items.append(
                RecentActivityItem(
                    activity_type="memory",
                    title=f"Memory · {m.category}",
                    description=_truncate(m.content, 120),
                    created_at=m.created_at,
                )
            )

        sim_result = await db.execute(
            select(ReviewSimulation)
            .where(ReviewSimulation.user_id == user_id)
            .order_by(ReviewSimulation.created_at.desc())
            .limit(3)
        )
        for s in sim_result.scalars().all():
            items.append(
                RecentActivityItem(
                    activity_type="simulation",
                    title=f"Review simulation · {s.rating}/5",
                    description=_truncate(s.review, 120),
                    created_at=s.created_at,
                )
            )

        imp_result = await db.execute(
            select(ContextImport)
            .where(ContextImport.user_id == user_id)
            .order_by(ContextImport.created_at.desc())
            .limit(3)
        )
        for imp in imp_result.scalars().all():
            items.append(
                RecentActivityItem(
                    activity_type="import",
                    title=f"Context import · {imp.source_platform or 'AI'}",
                    description=_truncate(imp.summary or imp.raw_content or "", 120),
                    created_at=imp.created_at,
                )
            )

        risk_result = await db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(3)
        )
        for risk in risk_result.scalars().all():
            items.append(
                RecentActivityItem(
                    activity_type="risk",
                    title=f"Risk assessment · {risk.risk_level}",
                    description=_truncate(risk.reasoning, 120),
                    created_at=risk.created_at,
                )
            )

        persona_result = await db.execute(
            select(Persona)
            .where(Persona.user_id == user_id)
            .order_by(Persona.created_at.desc())
            .limit(2)
        )
        for p in persona_result.scalars().all():
            items.append(
                RecentActivityItem(
                    activity_type="persona",
                    title=f"Persona · {p.persona_name}",
                    description=_truncate(p.reasoning, 120),
                    created_at=p.created_at,
                )
            )

        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:10]


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _profile_sleep_score(sleep_pattern: str | None) -> int:
    if not sleep_pattern:
        return 55
    s = sleep_pattern.lower()
    if "less than 5" in s:
        return 35
    if "5-6" in s or "5–6" in s:
        return 48
    if "6-7" in s or "6–7" in s:
        return 62
    if "7-8" in s or "7–8" in s:
        return 78
    if "8+" in s:
        return 88
    if "irregular" in s:
        return 45
    return 55


def _profile_stress_score(stress_level: str | None) -> int:
    if not stress_level:
        return 50
    return RISK_SCORES.get(stress_level.lower(), 50)


def _keyword_daily_scores(
    labels: list[str],
    memories: list[Memory],
    pattern: re.Pattern[str],
    baseline: int,
    boost: int,
) -> list[int]:
    counts = {label: 0 for label in labels}
    for mem in memories:
        if not pattern.search(mem.content or ""):
            continue
        day = mem.created_at.date().isoformat() if mem.created_at else None
        if day in counts:
            counts[day] += 1

    return [min(100, baseline + counts[label] * boost) for label in labels]
