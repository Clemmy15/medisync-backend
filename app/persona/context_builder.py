"""Aggregates profile, memory, imports, and behaviour for persona generation."""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from app.memory.categories import get_memory_label
from app.models.context_import import ContextImport
from app.models.memory import Memory
from app.models.profile import UserProfile
from app.persona.templates import PERSONA_SIGNAL_HINTS

logger = logging.getLogger(__name__)


@dataclass
class PersonaContextBundle:
    profile_section: str = ""
    memory_section: str = ""
    imports_section: str = ""
    behaviour_section: str = ""
    sources_used: list[str] = field(default_factory=list)

    @property
    def full_context(self) -> str:
        sections = [
            self.profile_section,
            self.memory_section,
            self.imports_section,
            self.behaviour_section,
        ]
        return "\n\n".join(s for s in sections if s.strip())

    @property
    def data_richness_score(self) -> float:
        """0-1 score based on available data sources."""
        score = 0.0
        if self.profile_section:
            score += 0.25
        if self.memory_section:
            score += 0.35
        if self.imports_section:
            score += 0.25
        if self.behaviour_section:
            score += 0.15
        return min(1.0, score)


class PersonaContextBuilder:
    @staticmethod
    def build(
        profile: UserProfile | None,
        memories: list[Memory],
        imports: list[ContextImport],
    ) -> PersonaContextBundle:
        bundle = PersonaContextBundle()

        if profile:
            bundle.profile_section = PersonaContextBuilder._format_profile(profile)
            bundle.sources_used.append("profile")

        if memories:
            bundle.memory_section = PersonaContextBuilder._format_memories(memories)
            bundle.sources_used.append("memory")
            bundle.behaviour_section = PersonaContextBuilder._derive_behaviour_patterns(
                memories
            )
            if bundle.behaviour_section:
                bundle.sources_used.append("behavioural_patterns")

        if imports:
            bundle.imports_section = PersonaContextBuilder._format_imports(imports)
            bundle.sources_used.append("imported_context")

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
    def _format_memories(memories: list[Memory]) -> str:
        grouped: dict[str, list[str]] = defaultdict(list)
        for memory in memories[:40]:
            grouped[memory.category].append(memory.content)

        lines = ["=== BEHAVIOURAL MEMORY ==="]
        for category, items in grouped.items():
            label = get_memory_label(category)
            lines.append(f"\n{label}:")
            for item in items[:8]:
                lines.append(f"  - {item}")
        return "\n".join(lines)

    @staticmethod
    def _format_imports(imports: list[ContextImport]) -> str:
        lines = ["=== IMPORTED AI CONTEXT ==="]
        for record in imports[:5]:
            platform = record.source_platform or "unknown"
            summary = record.summary or "No summary"
            lines.append(f"\n[{platform}] {summary}")
            if record.extracted_data:
                try:
                    data = json.loads(record.extracted_data)
                    for key in (
                        "symptoms", "habits", "health_goals",
                        "stress_indicators", "sleep_patterns",
                    ):
                        if values := data.get(key):
                            if isinstance(values, list) and values:
                                lines.append(f"  {key}: {', '.join(values[:3])}")
                except json.JSONDecodeError:
                    logger.debug("Could not parse import id=%s", record.id)
        return "\n".join(lines)

    @staticmethod
    def _derive_behaviour_patterns(memories: list[Memory]) -> str:
        """Heuristic behaviour signals from memory content."""
        combined = " ".join(m.content.lower() for m in memories)
        if not combined.strip():
            return ""

        signals: list[str] = []
        for persona, keywords in PERSONA_SIGNAL_HINTS.items():
            hits = sum(1 for kw in keywords if kw in combined)
            if hits >= 2:
                signals.append(f"{persona} signals (strength {hits})")

        recurring: dict[str, int] = defaultdict(int)
        for memory in memories:
            if len(memory.content) > 10:
                recurring[memory.category] += 1

        lines = ["=== BEHAVIOURAL PATTERNS ==="]
        if signals:
            lines.append("Detected persona signals: " + "; ".join(signals))
        if recurring:
            top = sorted(recurring.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append(
                "Dominant memory categories: "
                + ", ".join(f"{get_memory_label(k)} ({v})" for k, v in top)
            )
        return "\n".join(lines) if len(lines) > 1 else ""
