from fastapi import APIRouter

from app.api.routes import (
    admin,
    analysis,
    analytics,
    auth,
    context_import,
    dashboard,
    memory,
    persona,
    profile,
    reasoning,
    recommendations,
    review_simulation,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profile"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(
    context_import.router, prefix="/context-import", tags=["AI Context Import"]
)
api_router.include_router(
    memory.router, prefix="/memory", tags=["Behavioural Memory Engine"]
)
api_router.include_router(persona.router, prefix="/persona", tags=["Persona Engine"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(
    review_simulation.router, prefix="/simulation", tags=["Review Simulation"]
)
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(
    reasoning.router, prefix="/reasoning", tags=["Reasoning Traces"]
)
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
