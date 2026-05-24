"""Add composite indexes for analytics and list queries

Revision ID: 008
Revises: 007
Create Date: 2026-05-24

"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_memories_user_id_created_at",
        "memories",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_memories_user_id_category",
        "memories",
        ["user_id", "category"],
    )
    op.create_index(
        "ix_recommendations_user_id_created_at",
        "recommendations",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_recommendations_category",
        "recommendations",
        ["category"],
    )
    op.create_index(
        "ix_context_imports_user_id_created_at",
        "context_imports",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_personas_user_id_created_at",
        "personas",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_review_simulations_user_id_created_at",
        "review_simulations",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_reasoning_traces_user_id_trace_type",
        "reasoning_traces",
        ["user_id", "trace_type"],
    )
    op.create_index(
        "ix_reasoning_traces_created_at",
        "reasoning_traces",
        ["created_at"],
    )
    op.create_index(
        "ix_analytics_events_user_id_created_at",
        "analytics_events",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_risk_assessments_user_id_created_at",
        "risk_assessments",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_user_id_created_at", table_name="risk_assessments")
    op.drop_index("ix_analytics_events_user_id_created_at", table_name="analytics_events")
    op.drop_index("ix_reasoning_traces_created_at", table_name="reasoning_traces")
    op.drop_index("ix_reasoning_traces_user_id_trace_type", table_name="reasoning_traces")
    op.drop_index("ix_review_simulations_user_id_created_at", table_name="review_simulations")
    op.drop_index("ix_personas_user_id_created_at", table_name="personas")
    op.drop_index("ix_context_imports_user_id_created_at", table_name="context_imports")
    op.drop_index("ix_recommendations_category", table_name="recommendations")
    op.drop_index("ix_recommendations_user_id_created_at", table_name="recommendations")
    op.drop_index("ix_memories_user_id_category", table_name="memories")
    op.drop_index("ix_memories_user_id_created_at", table_name="memories")
