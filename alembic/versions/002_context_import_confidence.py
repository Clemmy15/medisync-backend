"""Add confidence fields to context_imports

Revision ID: 002
Revises: 001
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "context_imports",
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "context_imports",
        sa.Column("field_confidence", sa.Text(), nullable=True),
    )
    op.add_column(
        "context_imports",
        sa.Column("summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("context_imports", "summary")
    op.drop_column("context_imports", "field_confidence")
    op.drop_column("context_imports", "confidence_score")
