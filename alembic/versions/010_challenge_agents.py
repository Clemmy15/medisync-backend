"""Challenge agents: cold start, nigerian context, ranking, fidelity, evaluation

Revision ID: 010
Revises: 009
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nigerian_context_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("affordability_tier", sa.String(50), nullable=False),
        sa.Column("affordability_notes", sa.Text(), nullable=False),
        sa.Column("lifestyle_patterns", sa.Text(), nullable=False),
        sa.Column("communication_style", sa.Text(), nullable=False),
        sa.Column("contextual_reasoning", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nigerian_context_user", "nigerian_context_records", ["user_id"])

    op.create_table(
        "cold_start_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("persona", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cold_start_user", "cold_start_runs", ["user_id"])

    op.create_table(
        "recommendation_ranking_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("concern", sa.String(500), nullable=False),
        sa.Column("ranked_items_json", sa.Text(), nullable=False),
        sa.Column("ranking_metrics_json", sa.Text(), nullable=False),
        sa.Column("nigerian_context_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["nigerian_context_id"], ["nigerian_context_records.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ranking_batch_user", "recommendation_ranking_batches", ["user_id"])

    op.create_table(
        "explanations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("memory_snapshot", sa.Text(), nullable=False),
        sa.Column("persona_snapshot", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_explanation_entity", "explanations", ["entity_type", "entity_id"])

    op.create_table(
        "evaluation_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(20), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "orchestration_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("pipeline_steps_json", sa.Text(), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=False),
        sa.Column("explanation_id", sa.Integer(), nullable=True),
        sa.Column("ranking_batch_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["explanation_id"], ["explanations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["ranking_batch_id"], ["recommendation_ranking_batches.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column("review_simulations", sa.Column("fidelity_score", sa.Float(), nullable=True))
    op.add_column(
        "review_simulations", sa.Column("fidelity_evidence_json", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("review_simulations", "fidelity_evidence_json")
    op.drop_column("review_simulations", "fidelity_score")
    op.drop_table("orchestration_runs")
    op.drop_table("evaluation_reports")
    op.drop_table("explanations")
    op.drop_table("recommendation_ranking_batches")
    op.drop_table("cold_start_runs")
    op.drop_table("nigerian_context_records")
