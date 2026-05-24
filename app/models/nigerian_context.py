from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class NigerianContextRecord(Base):
    __tablename__ = "nigerian_context_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    affordability_tier: Mapped[str] = mapped_column(String(50), default="student_budget")
    affordability_notes: Mapped[str] = mapped_column(Text, nullable=False)
    lifestyle_patterns: Mapped[str] = mapped_column(Text, nullable=False)
    communication_style: Mapped[str] = mapped_column(Text, nullable=False)
    contextual_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="nigerian_context_records")
