from typing import Annotated



from fastapi import APIRouter, Depends, Query



from app.agents.behaviour_analysis_agent import BehaviourAnalysisAgent

from app.agents.risk_detection_agent import RiskDetectionAgent

from app.api.helpers import to_agent_result_schema

from app.core.deps import (

    get_behaviour_analysis_agent,

    get_current_user,

    get_risk_detection_agent,

    get_risk_detection_engine,

)

from app.core.exceptions import NotFoundError
from app.domain.enums import RiskLevel

from app.models.user import User

from app.risk_detection.engine import RiskDetectionEngine

from app.schemas.analysis import BehaviourAnalysisResult

from app.schemas.risk_detection import (

    RiskAssessmentHistoryItem,

    RiskDetectionRequest,

    RiskDetectionResponse,

    RiskDetectionResult,

)



router = APIRouter()





@router.post(

    "/behaviour",

    response_model=BehaviourAnalysisResult,

    summary="Analyze behavioural patterns and trends",

)

async def analyze_behaviour(

    current_user: Annotated[User, Depends(get_current_user)],

    agent: Annotated[BehaviourAnalysisAgent, Depends(get_behaviour_analysis_agent)],

) -> BehaviourAnalysisResult:

    result = await agent.run(current_user.id)

    return to_agent_result_schema(result, BehaviourAnalysisResult)





@router.post(

    "/risk",

    response_model=RiskDetectionResult,

    summary="Detect health risks from symptoms and behavioural data",

    description=(

        "Identifies **dangerous symptom patterns**, **behavioural deterioration**, "

        "and **recurring health concerns** using profile, persona, memory, and imports. "

        "Returns risk level: **low**, **moderate**, or **high**."

    ),

)

async def detect_risk(

    data: RiskDetectionRequest,

    current_user: Annotated[User, Depends(get_current_user)],

    agent: Annotated[RiskDetectionAgent, Depends(get_risk_detection_agent)],

) -> RiskDetectionResult:

    result = await agent.run(current_user.id, data)

    return to_agent_result_schema(result, RiskDetectionResult)





@router.get(

    "/risk/current",

    response_model=RiskDetectionResponse,

    summary="Get latest risk assessment",

)

async def get_current_risk(

    current_user: Annotated[User, Depends(get_current_user)],

    engine: Annotated[RiskDetectionEngine, Depends(get_risk_detection_engine)],

) -> RiskDetectionResponse:

    assessment = await engine.get_current(current_user.id)

    if not assessment:

        raise NotFoundError(

            "No risk assessment found. Call POST /analysis/risk first.",

        )

    from app.domain.enums import RiskLevel



    return RiskDetectionResponse(

        risk_level=RiskLevel(assessment.risk_level),

        reasoning=assessment.reasoning,

        recommended_action=assessment.recommended_action,

    )





@router.get(

    "/risk/history",

    response_model=list[RiskAssessmentHistoryItem],

    summary="Get risk assessment history",

)

async def get_risk_history(

    current_user: Annotated[User, Depends(get_current_user)],

    engine: Annotated[RiskDetectionEngine, Depends(get_risk_detection_engine)],

    limit: int = Query(default=50, ge=1, le=200),

) -> list[RiskAssessmentHistoryItem]:

    records = await engine.get_history(current_user.id, limit=limit)

    return [RiskAssessmentHistoryItem.from_orm(r) for r in records]


