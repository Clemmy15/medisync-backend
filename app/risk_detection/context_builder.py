"""Aggregates profile, persona, memory, and imports for risk detection."""

import json
from dataclasses import dataclass, field

from app.memory.categories import get_memory_label
from app.models.context_import import ContextImport
from app.models.memory import Memory
from app.models.persona import Persona
from app.models.profile import UserProfile


@dataclass
class RiskContextBundle:
    profile_section: str = ""
    persona_section: str = ""
    memory_section: str = ""
    imports_section: str = ""
    symptoms_section: str = ""
    sources_used: list[str] = field(default_factory=list)

    @property
    def full_context(self) -> str:
        sections = [
            self.profile_section,
            self.persona_section,
            self.memory_section,
            self.imports_section,
            self.symptoms_section,
        ]
        return "\n\n".join(s for s in sections if s.strip())


class RiskContextBuilder:
    @staticmethod
    def build(
        profile: UserProfile | None,
        persona: Persona | None,
        memories: list[Memory],
        imports: list[ContextImport],
        symptoms: list[str],
        extra_context: str | None = None,
    ) -> RiskContextBundle:
        bundle = RiskContextBundle()

        if profile:
            bundle.profile_section = RiskContextBuilder._format_profile(profile)
            bundle.sources_used.append("profile")

        if persona:
            bundle.persona_section = RiskContextBuilder._format_persona(persona)
            bundle.sources_used.append("persona")

        if memories:
            bundle.memory_section = RiskContextBuilder._format_memories(memories)
            bundle.sources_used.append("memory")

        if imports:
            bundle.imports_section = RiskContextBuilder._format_imports(imports)
            bundle.sources_used.append("imported_context")

        if symptoms:
            bundle.symptoms_section = (
                "=== REPORTED SYMPTOMS ===\n" + "\n".join(f"- {s}" for s in symptoms)
            )
        elif extra_context:
            bundle.symptoms_section = f"=== ADDITIONAL CONTEXT ===\n{extra_context}"

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
            f"Health goals: {profile.health_goals or 'unknown'}"
        )

    @staticmethod
    def _format_persona(persona: Persona) -> str:
        return (
            "=== USER PERSONA ===\n"
            f"Persona: {persona.persona_name}\n"
            f"Profile: {persona.persona_reasoning}"
        )

    @staticmethod
    def _format_memories(memories: list[Memory]) -> str:
        lines = ["=== BEHAVIOURAL & HEALTH MEMORY ==="]
        for memory in memories[:40]:
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
                    for key in ("symptoms", "stress_indicators", "sleep_patterns"):
                        items = data.get(key) or []
                        if items:
                            lines.append(f"  {key}: {', '.join(items[:5])}")
                except json.JSONDecodeError:
                    pass
        return "\n".join(lines)
