"""Canonical behavioural personas for classification."""

CANONICAL_PERSONAS: list[str] = [
    "Sleep-Deprived Student",
    "Busy Professional",
    "Fitness Enthusiast",
    "Budget-Conscious User",
    "Busy Parent",
    "Health-Conscious Senior",
    "Young Professional",
]

PERSONA_SIGNAL_HINTS: dict[str, list[str]] = {
    "Sleep-Deprived Student": [
        "student", "university", "exam", "late night", "sleep", "study",
    ],
    "Busy Professional": [
        "work", "deadline", "office", "career", "professional", "stress",
    ],
    "Fitness Enthusiast": [
        "gym", "exercise", "workout", "fitness", "run", "training",
    ],
    "Budget-Conscious User": [
        "budget", "affordable", "cost", "cheap", "save money", "price",
    ],
    "Busy Parent": [
        "parent", "children", "family", "kids", "childcare",
    ],
}
