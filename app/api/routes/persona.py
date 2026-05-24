from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.agents.persona_agent import PersonaAgent
from app.api.helpers import to_agent_result_schema
from app.core.deps import get_current_user, get_persona_agent, get_persona_engine
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.persona.engine import PersonaEngine
from app.schemas.persona import (
    PersonaGenerateResult,
    PersonaHistoryItem,
    PersonaResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=PersonaGenerateResult,
    summary="Generate user behavioural persona",
    description=(
        "Builds a persona from **profile data**, **behavioural memory**, "
        "**imported AI context**, and **derived behavioural patterns**. "
        "Stores result in persona history."
    ),
)
async def generate_persona(
    current_user: Annotated[User, Depends(get_current_user)],
    agent: Annotated[PersonaAgent, Depends(get_persona_agent)],
) -> PersonaGenerateResult:
    result = await agent.run(current_user.id)
    return to_agent_result_schema(result, PersonaGenerateResult)


@router.get(
    "/current",
    response_model=PersonaResponse,
    summary="Get the latest generated persona",
)
async def get_current_persona(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
) -> PersonaResponse:
    persona = await engine.get_current(current_user.id)
    if not persona:
        raise NotFoundError(
            "No persona generated yet. Call POST /persona/generate first.",
            details={"user_id": current_user.id},
        )
    return PersonaResponse.from_orm_persona(persona)


@router.get(
    "/history",
    response_model=list[PersonaHistoryItem],
    summary="Get persona generation history",
)
async def get_persona_history(
    current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[PersonaHistoryItem]:
    records = await engine.get_history(current_user.id, limit=limit)
    return [PersonaHistoryItem.from_orm_persona(p) for p in records]
