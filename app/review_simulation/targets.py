from app.domain.enums import SimulationTargetType

TARGET_TYPE_LABELS: dict[SimulationTargetType, str] = {
    SimulationTargetType.HEALTHCARE_APPS: "Healthcare App",
    SimulationTargetType.WELLNESS_PRODUCTS: "Wellness Product",
    SimulationTargetType.TELEMEDICINE_SERVICES: "Telemedicine Service",
    SimulationTargetType.PHARMACIES: "Pharmacy",
    SimulationTargetType.FITNESS_PROGRAMS: "Fitness Program",
}

TARGET_SIMULATION_HINTS: dict[SimulationTargetType, str] = {
    SimulationTargetType.HEALTHCARE_APPS: (
        "Focus on UX, notifications, data accuracy, privacy, and daily engagement."
    ),
    SimulationTargetType.WELLNESS_PRODUCTS: (
        "Focus on ingredients, efficacy claims, value, side effects, and routine fit."
    ),
    SimulationTargetType.TELEMEDICINE_SERVICES: (
        "Focus on wait times, doctor quality, prescription process, and convenience."
    ),
    SimulationTargetType.PHARMACIES: (
        "Focus on stock availability, pricing, delivery, pharmacist advice, and trust."
    ),
    SimulationTargetType.FITNESS_PROGRAMS: (
        "Focus on workout variety, motivation, progress tracking, and schedule fit."
    ),
}


def get_target_label(target: SimulationTargetType) -> str:
    return TARGET_TYPE_LABELS[target]
