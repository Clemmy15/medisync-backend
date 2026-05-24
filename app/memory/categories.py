from app.domain.enums import MemoryCategory

MEMORY_TYPE_LABELS: dict[MemoryCategory, str] = {
    MemoryCategory.HEALTH: "Health Memory",
    MemoryCategory.BEHAVIOUR: "Behaviour Memory",
    MemoryCategory.RECOMMENDATION: "Recommendation Memory",
    MemoryCategory.COMMUNICATION: "Communication Memory",
}


def get_memory_label(category: str | MemoryCategory) -> str:
    try:
        cat = category if isinstance(category, MemoryCategory) else MemoryCategory(category)
        return MEMORY_TYPE_LABELS[cat]
    except ValueError:
        return str(category)
