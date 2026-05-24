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
    HEALTH_APPS = "health_apps"
    WELLNESS_PLANS = "wellness_plans"
    PRODUCTIVITY_WELLNESS = "productivity_wellness"
    SLEEP_IMPROVEMENT = "sleep_improvement"
    HYDRATION_IMPROVEMENT = "hydration_improvement"
    STRESS_REDUCTION = "stress_reduction"
