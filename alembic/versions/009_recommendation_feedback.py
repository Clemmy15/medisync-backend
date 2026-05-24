"""Add recommendation save and helpful feedback columns

Revision ID: 009
Revises: 008
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("is_saved", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "recommendations",
        sa.Column("marked_helpful", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "marked_helpful")
    op.drop_column("recommendations", "is_saved")
