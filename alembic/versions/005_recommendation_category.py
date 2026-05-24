"""Add category and sources_used to recommendations

Revision ID: 005
Revises: 004
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("category", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("sources_used", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE recommendations SET category = 'wellness_plans' WHERE category IS NULL"
    )
    op.alter_column("recommendations", "category", nullable=False)
    op.create_index("ix_recommendations_category", "recommendations", ["category"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_category", table_name="recommendations")
    op.drop_column("recommendations", "sources_used")
    op.drop_column("recommendations", "category")
