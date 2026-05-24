from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RecommendationRankingBatch(Base):
    __tablename__ = "recommendation_ranking_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concern: Mapped[str] = mapped_column(String(500), nullable=False)
    ranked_items_json: Mapped[str] = mapped_column(Text, nullable=False)
    ranking_metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    nigerian_context_id: Mapped[int | None] = mapped_column(
        ForeignKey("nigerian_context_records.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="ranking_batches")
