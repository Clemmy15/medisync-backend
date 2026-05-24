"""Add risk_assessments table

Revision ID: 007
Revises: 006
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("reported_symptoms", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_assessments_user_id", "risk_assessments", ["user_id"]
    )
    op.create_index(
        "ix_risk_assessments_risk_level", "risk_assessments", ["risk_level"]
    )


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_risk_level", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_user_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
