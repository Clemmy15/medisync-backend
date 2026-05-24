"""Confidence scoring for extracted health context."""

from typing import Any

from app.schemas.context_import import FieldConfidenceScores

FIELD_KEYWORDS: dict[str, list[str]] = {
    "symptoms": [
        "symptom", "pain", "headache", "fatigue", "fever", "nausea", "ache", "ill",
    ],
    "habits": [
        "habit", "exercise", "diet", "routine", "meal", "walk", "run", "gym",
    ],
    "sleep_patterns": [
        "sleep", "insomnia", "bedtime", "wake", "nap", "rest",
    ],
    "hydration_behaviour": [
        "water", "hydrat", "drink", "fluid", "dehydrat",
    ],
    "stress_indicators": [
        "stress", "anxiety", "overwhelm", "burnout", "pressure", "deadline",
    ],
    "communication_preferences": [
        "prefer", "communication", "concise", "detail", "tone", "format",
    ],
    "health_goals": [
        "goal", "aim", "target", "improve", "reduce", "increase", "achieve",
    ],
}


def _keyword_boost(field: str, raw_content: str) -> float:
    lowered = raw_content.lower()
    keywords = FIELD_KEYWORDS.get(field, [])
    hits = sum(1 for kw in keywords if kw in lowered)
    return min(0.15, hits * 0.03)


def score_field(
    items: list[str],
    raw_content: str,
    llm_score: float | None = None,
) -> float:
    """Score confidence for a single extracted field (0.0–1.0)."""
    if llm_score is not None:
        base = max(0.0, min(1.0, float(llm_score)))
    elif not items:
        return 0.0
    else:
        # More items with substantive text → higher base confidence
        substantive = [i for i in items if len(i.strip()) > 3]
        base = 0.45 + min(0.35, len(substantive) * 0.08)
        avg_len = sum(len(i) for i in substantive) / max(len(substantive), 1)
        base += min(0.15, avg_len / 200)

    return round(min(0.99, base), 3)


def score_field_named(
    field: str,
    items: list[str],
    raw_content: str,
    llm_score: float | None = None,
) -> float:
    score = score_field(items, raw_content, llm_score)
    if items:
        score = min(0.99, score + _keyword_boost(field, raw_content))
    return round(score, 3)


def build_field_confidence(
    extracted: dict[str, list[str]],
    raw_content: str,
    llm_field_scores: dict[str, Any] | None = None,
) -> FieldConfidenceScores:
    llm_scores = llm_field_scores or {}

    legacy_map = {
        "sleep_patterns": "sleep_behaviour",
        "stress_indicators": "stress_patterns",
        "hydration_behaviour": "hydration_habits",
    }

    def _score(field: str, items: list[str]) -> float:
        llm_val = llm_scores.get(field)
        if llm_val is None:
            llm_val = llm_scores.get(legacy_map.get(field, ""))
        return score_field_named(field, items, raw_content, llm_val)

    return FieldConfidenceScores(
        symptoms=_score("symptoms", extracted.get("symptoms", [])),
        habits=_score("habits", extracted.get("habits", [])),
        sleep_patterns=_score("sleep_patterns", extracted.get("sleep_patterns", [])),
        hydration_behaviour=_score(
            "hydration_behaviour", extracted.get("hydration_behaviour", [])
        ),
        stress_indicators=_score(
            "stress_indicators", extracted.get("stress_indicators", [])
        ),
        communication_preferences=_score(
            "communication_preferences", extracted.get("communication_preferences", [])
        ),
        health_goals=_score("health_goals", extracted.get("health_goals", [])),
    )


def compute_overall_confidence(
    field_scores: FieldConfidenceScores,
    llm_overall: float | None = None,
) -> float:
    """Weighted overall confidence from per-field scores."""
    values = [
        field_scores.symptoms,
        field_scores.habits,
        field_scores.sleep_patterns,
        field_scores.hydration_behaviour,
        field_scores.stress_indicators,
        field_scores.communication_preferences,
        field_scores.health_goals,
    ]
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return 0.0

    heuristic = sum(non_zero) / len(non_zero)
    if llm_overall is not None:
        llm_overall = max(0.0, min(1.0, float(llm_overall)))
        return round(0.4 * heuristic + 0.6 * llm_overall, 3)
    return round(heuristic, 3)
