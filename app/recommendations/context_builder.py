"""Aggregates profile, persona, memory, and imports for recommendation generation."""

import json
import logging
from dataclasses import dataclass, field

from app.domain.enums import RecommendationCategory
from app.memory.categories import get_memory_label
from app.models.context_import import ContextImport
from app.models.memory import Memory
from app.models.persona import Persona
from app.models.profile import UserProfile

logger = logging.getLogger(__name__)

CATEGORY_FOCUS: dict[RecommendationCategory, str] = {
    RecommendationCategory.HEALTH_APPS: (
        "Recommend mobile apps or digital tools for health tracking and management."
    ),
    RecommendationCategory.WELLNESS_PLANS: (
        "Recommend holistic wellness plans combining diet, activity, and mindfulness."
    ),
    RecommendationCategory.PRODUCTIVITY_WELLNESS: (
        "Recommend ways to balance productivity with health (breaks, ergonomics, focus)."
    ),
    RecommendationCategory.SLEEP_IMPROVEMENT: (
        "Recommend sleep hygiene, schedules, and tools to improve sleep quality."
    ),
    RecommendationCategory.HYDRATION_IMPROVEMENT: (
        "Recommend hydration habits, reminders, and measurable daily water goals."
    ),
    RecommendationCategory.STRESS_REDUCTION: (
        "Recommend stress management techniques, routines, and coping strategies."
    ),
}


@dataclass
class RecommendationContextBundle:
    profile_section: str = ""
    persona_section: str = ""
    memory_section: str = ""
    imports_section: str = ""
    category_focus: str = ""
    sources_used: list[str] = field(default_factory=list)

    @property
    def full_context(self) -> str:
        sections = [
            self.profile_section,
            self.persona_section,
            self.memory_section,
            self.imports_section,
            self.category_focus,
        ]
        return "\n\n".join(s for s in sections if s.strip())

    @property
    def data_richness_score(self) -> float:
        score = 0.0
        if self.profile_section:
            score += 0.2
        if self.persona_section:
            score += 0.2
        if self.memory_section:
            score += 0.35
        if self.imports_section:
            score += 0.25
        return min(1.0, score)


class RecommendationContextBuilder:
    @staticmethod
    def build(
        profile: UserProfile | None,
        persona: Persona | None,
        memories: list[Memory],
        imports: list[ContextImport],
        category: RecommendationCategory | None = None,
    ) -> RecommendationContextBundle:
        bundle = RecommendationContextBundle()

        if profile:
            bundle.profile_section = RecommendationContextBuilder._format_profile(profile)
            bundle.sources_used.append("profile")

        if persona:
            bundle.persona_section = RecommendationContextBuilder._format_persona(persona)
            bundle.sources_used.append("persona")

        if memories:
            bundle.memory_section = RecommendationContextBuilder._format_memories(memories)
            bundle.sources_used.append("memory")

        if imports:
            bundle.imports_section = RecommendationContextBuilder._format_imports(imports)
            bundle.sources_used.append("imported_context")

        if category:
            bundle.category_focus = (
                f"=== RECOMMENDATION FOCUS ===\n"
                f"Category: {category.value}\n"
                f"{CATEGORY_FOCUS[category]}"
            )
        else:
            bundle.category_focus = (
                "=== RECOMMENDATION FOCUS ===\n"
                "Choose the most relevant category from: health_apps, wellness_plans, "
                "productivity_wellness, sleep_improvement, hydration_improvement, "
                "stress_reduction."
            )

        return bundle

    @staticmethod
    def _format_profile(profile: UserProfile) -> str:
        return (
            "=== USER PROFILE ===\n"
            f"Age range: {profile.age_range or 'unknown'}\n"
            f"Occupation: {profile.occupation or 'unknown'}\n"
            f"Stress level: {profile.stress_level or 'unknown'}\n"
            f"Sleep pattern: {profile.sleep_pattern or 'unknown'}\n"
            f"Hydration: {profile.hydration_level or 'unknown'}\n"
            f"Activity: {profile.activity_level or 'unknown'}\n"
            f"Diet: {profile.dietary_preferences or 'unknown'}\n"
            f"Health goals: {profile.health_goals or 'unknown'}\n"
            f"Communication style: {profile.communication_style or 'unknown'}"
        )

    @staticmethod
    def _format_persona(persona: Persona) -> str:
        return (
            "=== USER PERSONA ===\n"
            f"Persona: {persona.persona_name}\n"
            f"Reasoning: {persona.persona_reasoning}\n"
            f"Confidence: {persona.confidence_score:.2f}"
        )

    @staticmethod
    def _format_memories(memories: list[Memory]) -> str:
        lines = ["=== BEHAVIOURAL MEMORY ==="]
        for memory in memories[:30]:
            label = get_memory_label(memory.category)
            lines.append(f"- [{label}] {memory.content}")
        return "\n".join(lines)

    @staticmethod
    def _format_imports(imports: list[ContextImport]) -> str:
        lines = ["=== IMPORTED AI CONTEXT ==="]
        for record in imports[:5]:
            platform = record.source_platform or "unknown"
            summary = record.summary or "No summary"
            lines.append(f"[{platform}] {summary}")
            if record.extracted_data:
                try:
                    data = json.loads(record.extracted_data)
                    goals = data.get("health_goals") or data.get("goals") or []
                    if goals:
                        lines.append(f"  Goals: {', '.join(goals[:3])}")
                except json.JSONDecodeError:
                    pass
        return "\n".join(lines)
