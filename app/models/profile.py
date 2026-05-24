from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    age_range: Mapped[str | None] = mapped_column(String(50))
    occupation: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[str | None] = mapped_column(String(50))
    stress_level: Mapped[str | None] = mapped_column(String(50))
    sleep_pattern: Mapped[str | None] = mapped_column(String(100))
    hydration_level: Mapped[str | None] = mapped_column(String(50))
    activity_level: Mapped[str | None] = mapped_column(String(50))
    dietary_preferences: Mapped[str | None] = mapped_column(Text)
    health_goals: Mapped[str | None] = mapped_column(Text)
    communication_style: Mapped[str | None] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="profile")
