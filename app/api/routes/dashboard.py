from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    get_current_user,
    get_dashboard_engine,
    get_db,
)
from app.dashboard.engine import DashboardEngine
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse

router = APIRouter()


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    summary="User dashboard overview",
    description=(
        "Persona, health summary, risk level, recommendation count, recent activity, "
        "and Chart.js-ready sleep/stress/recommendation trend series (14 days)."
    ),
)
async def get_dashboard_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    engine: Annotated[DashboardEngine, Depends(get_dashboard_engine)],
) -> DashboardOverviewResponse:
    return await engine.get_overview(db, current_user.id)
