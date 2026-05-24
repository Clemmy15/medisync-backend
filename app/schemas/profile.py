from datetime import datetime

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    age_range: str | None = None
    occupation: str | None = None
    gender: str | None = None
    stress_level: str | None = None
    sleep_pattern: str | None = None
    hydration_level: str | None = None
    activity_level: str | None = None
    dietary_preferences: str | None = None
    health_goals: str | None = None
    communication_style: str | None = None


class ProfileUpdate(BaseModel):
    age_range: str | None = None
    occupation: str | None = None
    gender: str | None = None
    stress_level: str | None = None
    sleep_pattern: str | None = None
    hydration_level: str | None = None
    activity_level: str | None = None
    dietary_preferences: str | None = None
    health_goals: str | None = None
    communication_style: str | None = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    age_range: str | None
    occupation: str | None
    gender: str | None
    stress_level: str | None
    sleep_pattern: str | None
    hydration_level: str | None
    activity_level: str | None
    dietary_preferences: str | None
    health_goals: str | None
    communication_style: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}
