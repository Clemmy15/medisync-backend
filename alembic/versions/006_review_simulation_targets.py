"""Extend review_simulations for target types and service description

Revision ID: 006
Revises: 005
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "review_simulations",
        sa.Column("target_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "review_simulations",
        sa.Column("service_description", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE review_simulations SET target_type = 'healthcare_apps' "
        "WHERE target_type IS NULL"
    )
    op.alter_column("review_simulations", "target_type", nullable=False)
    op.alter_column(
        "review_simulations",
        "product_description",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.create_index(
        "ix_review_simulations_target_type",
        "review_simulations",
        ["target_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_review_simulations_target_type", table_name="review_simulations")
    op.alter_column(
        "review_simulations",
        "product_description",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("review_simulations", "service_description")
    op.drop_column("review_simulations", "target_type")
