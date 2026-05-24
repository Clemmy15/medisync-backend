from enum import Enum


class MemoryCategory(str, Enum):
    BEHAVIOUR = "behaviour"
    HEALTH = "health"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AIPlatform(str, Enum):
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CLAUDE = "claude"


class SimulationTargetType(str, Enum):
    HEALTHCARE_APPS = "healthcare_apps"
    WELLNESS_PRODUCTS = "wellness_products"
    TELEMEDICINE_SERVICES = "telemedicine_services"
    PHARMACIES = "pharmacies"
    FITNESS_PROGRAMS = "fitness_programs"


class RecommendationCategory(str, Enum):
    """Cross-domain recommendation categories (DSN challenge)."""

    HEALTH_APPS = "health_apps"
    WELLNESS_PRODUCTS = "wellness_products"
    WELLNESS_PLANS = "wellness_plans"
    EDUCATIONAL_CONTENT = "educational_content"
    FOOD_NUTRITION = "food_nutrition"
    EXERCISE_PLANS = "exercise_plans"
    PRODUCTIVITY_HABITS = "productivity_habits"
    PRODUCTIVITY_WELLNESS = "productivity_wellness"
    TELEMEDICINE_SERVICES = "telemedicine_services"
    SLEEP_IMPROVEMENT = "sleep_improvement"
    HYDRATION_IMPROVEMENT = "hydration_improvement"
    STRESS_REDUCTION = "stress_reduction"


# Canonical cross-domain set for ranking
CROSS_DOMAIN_CATEGORIES: tuple[RecommendationCategory, ...] = (
    RecommendationCategory.HEALTH_APPS,
    RecommendationCategory.WELLNESS_PRODUCTS,
    RecommendationCategory.EDUCATIONAL_CONTENT,
    RecommendationCategory.FOOD_NUTRITION,
    RecommendationCategory.EXERCISE_PLANS,
    RecommendationCategory.PRODUCTIVITY_HABITS,
    RecommendationCategory.TELEMEDICINE_SERVICES,
)


class ExplanationEntityType(str, Enum):
    RECOMMENDATION = "recommendation"
    REVIEW_SIMULATION = "review_simulation"
    COLD_START = "cold_start"
    RANKING_BATCH = "ranking_batch"
    ORCHESTRATION = "orchestration"


class EvaluationTaskType(str, Enum):
    TASK_A = "task_a"
    TASK_B = "task_b"


class OrchestrationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
