from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    memories = relationship("Memory", back_populates="user")
    personas = relationship("Persona", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    context_imports = relationship("ContextImport", back_populates="user")
    cold_start_runs = relationship("ColdStartRun", back_populates="user")
    nigerian_context_records = relationship("NigerianContextRecord", back_populates="user")
    ranking_batches = relationship("RecommendationRankingBatch", back_populates="user")
    explanations = relationship("Explanation", back_populates="user")
    evaluation_reports = relationship("EvaluationReport", back_populates="user")
    orchestration_runs = relationship("OrchestrationRun", back_populates="user")
