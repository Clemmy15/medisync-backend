from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_explanation_service
from app.explanations.service import ExplanationService
from app.models.user import User
from app.schemas.explanations import ExplanationResponse

router = APIRouter()


@router.get(
    "/{explanation_id}",
    response_model=ExplanationResponse,
    summary="Get explanation by ID",
    description=(
        "Returns reasoning, retrieved memory, persona, and confidence score "
        "for a stored explanation record."
    ),
)
async def get_explanation(
    explanation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExplanationService, Depends(get_explanation_service)],
) -> ExplanationResponse:
    return await service.get_by_id(current_user.id, explanation_id)
