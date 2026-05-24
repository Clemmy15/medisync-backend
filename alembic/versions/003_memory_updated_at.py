"""Add updated_at to memories

Revision ID: 003
Revises: 002
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "memories",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index("ix_memories_category", "memories", ["category"])


def downgrade() -> None:
    op.drop_index("ix_memories_category", table_name="memories")
    op.drop_column("memories", "updated_at")
