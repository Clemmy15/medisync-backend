"""Unit tests for Behavioural Memory Engine."""

import pytest

from app.domain.enums import MemoryCategory
from app.memory.behavioural_engine import BehaviouralMemoryEngine
from app.memory.categories import MEMORY_TYPE_LABELS, get_memory_label
from app.models.memory import Memory


class TestMemoryCategories:
    def test_all_four_types_labeled(self) -> None:
        assert len(MEMORY_TYPE_LABELS) == 4
        assert get_memory_label(MemoryCategory.HEALTH) == "Health Memory"
        assert get_memory_label(MemoryCategory.BEHAVIOUR) == "Behaviour Memory"


class TestRelevanceScoring:
    def test_distance_to_relevance(self) -> None:
        assert BehaviouralMemoryEngine._distance_to_relevance(0.0) == 1.0
        assert BehaviouralMemoryEngine._distance_to_relevance(1.0) == 0.5
        assert BehaviouralMemoryEngine._distance_to_relevance(None) == 0.5


class TestHeuristicSummary:
    def test_category_summary_preview(self) -> None:
        memories = [
            Memory(
                id=1,
                user_id=1,
                category="health",
                content="headaches",
            ),
            Memory(
                id=2,
                user_id=1,
                category="health",
                content="fatigue",
            ),
        ]
        summary = BehaviouralMemoryEngine._heuristic_category_summary(memories)
        assert "headaches" in summary
        assert "fatigue" in summary
