"""Hackathon Evaluation Module — Task A (reviews) and Task B (ranking)."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.enums import EvaluationTaskType
from app.evaluation.metrics import build_ranking_metrics, ndcg_at_k
from app.models.evaluation_report import EvaluationReport
from app.models.recommendation_batch import RecommendationRankingBatch
from app.models.review_simulation import ReviewSimulation
from app.schemas.evaluation import (
    EvaluationReportResponse,
    TaskAEvaluationRequest,
    TaskAMetrics,
    TaskBEvaluationRequest,
    TaskBMetrics,
)
from app.utils.json_helpers import safe_json_loads

logger = logging.getLogger(__name__)


class EvaluationEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def evaluate_task_a(
        self, user_id: int, request: TaskAEvaluationRequest
    ) -> EvaluationReportResponse:
        simulation = await self._get_simulation(user_id, request.simulation_id)
        fidelity = simulation.fidelity_score or 0.75
        rating_accuracy = 1.0
        if request.expected_rating is not None:
            diff = abs(simulation.rating - request.expected_rating)
            rating_accuracy = max(0.0, 1.0 - diff * 0.25)

        review_len = len(simulation.review or "")
        review_quality = min(1.0, 0.5 + review_len / 400)

        metrics = TaskAMetrics(
            rating_accuracy=round(rating_accuracy, 4),
            behavioural_fidelity=round(fidelity, 4),
            review_quality_score=round(review_quality, 4),
        )
        report_body = {
            "simulation_id": simulation.id,
            "persona_name": simulation.persona_name,
            "rating": simulation.rating,
            "fidelity_evidence": safe_json_loads(simulation.fidelity_evidence_json)
            or [],
            "summary": (
                "Task A evaluation: review simulation rating accuracy, "
                "behavioural fidelity, and review quality."
            ),
        }
        stored = await self._persist_report(
            user_id,
            EvaluationTaskType.TASK_A.value,
            metrics.model_dump(),
            report_body,
        )
        return self._to_response(stored)

    async def evaluate_task_b(
        self, user_id: int, request: TaskBEvaluationRequest
    ) -> EvaluationReportResponse:
        batch = await self._get_batch(user_id, request.batch_id)
        items = safe_json_loads(batch.ranked_items_json) or []
        relevances = request.relevance_scores
        if relevances is None:
            relevances = [float(i.get("confidence", 0.75)) for i in items]

        base_metrics = build_ranking_metrics(
            [
                {
                    "category": i.get("category", ""),
                    "confidence": rel,
                }
                for i, rel in zip(items, relevances, strict=False)
            ]
        )
        contextual = round(
            sum(relevances) / max(1, len(relevances)), 4
        ) if relevances else 0.0

        metrics = TaskBMetrics(
            **base_metrics,
            contextual_relevance=contextual,
        )
        report_body = {
            "batch_id": batch.id,
            "concern": batch.concern,
            "item_count": len(items),
            "ndcg_detail": ndcg_at_k(relevances, 10),
            "summary": (
                "Task B evaluation: cross-domain ranking quality, diversity, "
                "and contextual relevance."
            ),
        }
        stored = await self._persist_report(
            user_id,
            EvaluationTaskType.TASK_B.value,
            metrics.model_dump(),
            report_body,
        )
        return self._to_response(stored)

    async def _get_simulation(
        self, user_id: int, simulation_id: int | None
    ) -> ReviewSimulation:
        if simulation_id:
            stmt = select(ReviewSimulation).where(
                ReviewSimulation.id == simulation_id,
                ReviewSimulation.user_id == user_id,
            )
        else:
            stmt = (
                select(ReviewSimulation)
                .where(ReviewSimulation.user_id == user_id)
                .order_by(ReviewSimulation.created_at.desc())
                .limit(1)
            )
        row = (await self._db.execute(stmt)).scalar_one_or_none()
        if not row:
            raise NotFoundError("Review simulation not found")
        return row

    async def _get_batch(
        self, user_id: int, batch_id: int | None
    ) -> RecommendationRankingBatch:
        if batch_id:
            stmt = select(RecommendationRankingBatch).where(
                RecommendationRankingBatch.id == batch_id,
                RecommendationRankingBatch.user_id == user_id,
            )
        else:
            stmt = (
                select(RecommendationRankingBatch)
                .where(RecommendationRankingBatch.user_id == user_id)
                .order_by(RecommendationRankingBatch.created_at.desc())
                .limit(1)
            )
        row = (await self._db.execute(stmt)).scalar_one_or_none()
        if not row:
            raise NotFoundError("Ranking batch not found")
        return row

    async def _persist_report(
        self,
        user_id: int,
        task_type: str,
        metrics: dict,
        report: dict,
    ) -> EvaluationReport:
        record = EvaluationReport(
            user_id=user_id,
            task_type=task_type,
            metrics_json=json.dumps(metrics),
            report_json=json.dumps(report),
        )
        self._db.add(record)
        await self._db.flush()
        logger.info("Evaluation report %s task=%s", record.id, task_type)
        return record

    @staticmethod
    def _to_response(record: EvaluationReport) -> EvaluationReportResponse:
        return EvaluationReportResponse(
            id=record.id,
            task_type=record.task_type,
            metrics=safe_json_loads(record.metrics_json) or {},
            report=safe_json_loads(record.report_json) or {},
            created_at=record.created_at,
        )
