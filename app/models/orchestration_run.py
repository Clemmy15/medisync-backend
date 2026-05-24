from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OrchestrationRun(Base):
    __tablename__ = "orchestration_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="completed")
    pipeline_steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_summary: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_id: Mapped[int | None] = mapped_column(
        ForeignKey("explanations.id", ondelete="SET NULL"), nullable=True
    )
    ranking_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommendation_ranking_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="orchestration_runs")
