from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.behaviour_analysis_agent import BehaviourAnalysisAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.persona_agent import PersonaAgent
from app.persona.engine import PersonaEngine
from app.repositories.persona_repository import PersonaRepository
from app.agents.recommendation_agent import RecommendationAgent
from app.recommendations.engine import RecommendationEngine
from app.repositories.recommendation_repository import RecommendationRepository
from app.agents.review_simulation_agent import ReviewSimulationAgent
from app.repositories.review_simulation_repository import ReviewSimulationRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.review_simulation.engine import ReviewSimulationEngine
from app.risk_detection.engine import RiskDetectionEngine
from app.agents.risk_detection_agent import RiskDetectionAgent
from app.context_import.extractor import ContextExtractor
from app.context_import.service import ContextImportService
from app.repositories.context_import_repository import ContextImportRepository
from app.core.security import decode_access_token
from app.database.session import get_db
from app.memory.chroma_store import ChromaMemoryStore, get_chroma_store
from app.models.user import User
from app.repositories.memory_repository import MemoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.dashboard.engine import DashboardEngine
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.reasoning_service import ReasoningService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# --- Service & repository DI ---


def get_llm_service() -> LLMService:
    return LLMService()


def get_reasoning_service() -> ReasoningService:
    return ReasoningService()


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


def get_chroma_store_dep() -> ChromaMemoryStore:
    return get_chroma_store()


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_profile_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRepository:
    return ProfileRepository(db)


def get_memory_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemoryRepository:
    return MemoryRepository(db)


def get_context_extractor(
    llm: Annotated[LLMService, Depends(get_llm_service)],
) -> ContextExtractor:
    return ContextExtractor(llm)


def get_context_import_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContextImportRepository:
    return ContextImportRepository(db)


def get_memory_agent(
    db: Annotated[AsyncSession, Depends(get_db)],
    chroma: Annotated[ChromaMemoryStore, Depends(get_chroma_store_dep)],
    memory_repo: Annotated[MemoryRepository, Depends(get_memory_repository)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
) -> MemoryAgent:
    return MemoryAgent(db, chroma, memory_repo, profile_repo, reasoning)


def get_context_import_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    extractor: Annotated[ContextExtractor, Depends(get_context_extractor)],
    memory_agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    import_repo: Annotated[ContextImportRepository, Depends(get_context_import_repository)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
) -> ContextImportService:
    return ContextImportService(
        db, extractor, memory_agent, import_repo, analytics, reasoning
    )


def get_persona_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonaRepository:
    return PersonaRepository(db)


def get_persona_engine(
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    memory_agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    import_repo: Annotated[ContextImportRepository, Depends(get_context_import_repository)],
    persona_repo: Annotated[PersonaRepository, Depends(get_persona_repository)],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
) -> PersonaEngine:
    return PersonaEngine(
        db,
        llm,
        memory_agent.engine,
        profile_repo,
        import_repo,
        persona_repo,
        reasoning,
    )


def get_persona_agent(
    engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
) -> PersonaAgent:
    return PersonaAgent(engine)


def get_recommendation_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationRepository:
    return RecommendationRepository(db)


def get_recommendation_engine(
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    memory_agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    persona_engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    import_repo: Annotated[ContextImportRepository, Depends(get_context_import_repository)],
    recommendation_repo: Annotated[
        RecommendationRepository, Depends(get_recommendation_repository)
    ],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> RecommendationEngine:
    return RecommendationEngine(
        db,
        llm,
        memory_agent.engine,
        persona_engine,
        profile_repo,
        import_repo,
        recommendation_repo,
        reasoning,
        analytics,
    )


def get_recommendation_agent(
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
) -> RecommendationAgent:
    return RecommendationAgent(engine)


def get_review_simulation_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewSimulationRepository:
    return ReviewSimulationRepository(db)


def get_review_simulation_engine(
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    persona_engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
    simulation_repo: Annotated[
        ReviewSimulationRepository, Depends(get_review_simulation_repository)
    ],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ReviewSimulationEngine:
    return ReviewSimulationEngine(
        db, llm, persona_engine, simulation_repo, reasoning, analytics
    )


def get_review_simulation_agent(
    engine: Annotated[ReviewSimulationEngine, Depends(get_review_simulation_engine)],
) -> ReviewSimulationAgent:
    return ReviewSimulationAgent(engine)


def get_behaviour_analysis_agent(
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    memory_agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
) -> BehaviourAnalysisAgent:
    return BehaviourAnalysisAgent(db, llm, memory_agent, reasoning)


def get_risk_assessment_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskAssessmentRepository:
    return RiskAssessmentRepository(db)


def get_risk_detection_engine(
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMService, Depends(get_llm_service)],
    memory_agent: Annotated[MemoryAgent, Depends(get_memory_agent)],
    persona_engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repository)],
    import_repo: Annotated[ContextImportRepository, Depends(get_context_import_repository)],
    assessment_repo: Annotated[
        RiskAssessmentRepository, Depends(get_risk_assessment_repository)
    ],
    reasoning: Annotated[ReasoningService, Depends(get_reasoning_service)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> RiskDetectionEngine:
    return RiskDetectionEngine(
        db,
        llm,
        memory_agent.engine,
        persona_engine,
        profile_repo,
        import_repo,
        assessment_repo,
        reasoning,
        analytics,
    )


def get_risk_detection_agent(
    engine: Annotated[RiskDetectionEngine, Depends(get_risk_detection_engine)],
) -> RiskDetectionAgent:
    return RiskDetectionAgent(engine)


def get_dashboard_engine(
    persona_engine: Annotated[PersonaEngine, Depends(get_persona_engine)],
    risk_engine: Annotated[RiskDetectionEngine, Depends(get_risk_detection_engine)],
    recommendation_engine: Annotated[
        RecommendationEngine, Depends(get_recommendation_engine)
    ],
) -> DashboardEngine:
    return DashboardEngine(persona_engine, risk_engine, recommendation_engine)
