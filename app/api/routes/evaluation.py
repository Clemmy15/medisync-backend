from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_evaluation_engine
from app.evaluation.engine import EvaluationEngine
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationReportResponse,
    TaskAEvaluationRequest,
    TaskBEvaluationRequest,
)

router = APIRouter()


@router.post(
    "/task-a",
    response_model=EvaluationReportResponse,
    summary="Task A — review simulation evaluation",
    description="Evaluates rating accuracy, behavioural fidelity, and review quality.",
)
async def evaluate_task_a(
    data: TaskAEvaluationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[EvaluationEngine, Depends(get_evaluation_engine)],
) -> EvaluationReportResponse:
    return await engine.evaluate_task_a(current_user.id, data)


@router.post(
    "/task-b",
    response_model=EvaluationReportResponse,
    summary="Task B — recommendation ranking evaluation",
    description=(
        "Evaluates NDCG@10, hit rate, recommendation diversity, "
        "and contextual relevance."
    ),
)
async def evaluate_task_b(
    data: TaskBEvaluationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[EvaluationEngine, Depends(get_evaluation_engine)],
) -> EvaluationReportResponse:
    return await engine.evaluate_task_b(current_user.id, data)
