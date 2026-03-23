"""add refresh token binding hash

Revision ID: 20260323_01
Revises: 20260304_01
Create Date: 2026-03-23 00:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260323_01"
down_revision: Union[str, None] = "20260304_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("client_binding_hash", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("refresh_tokens", "client_binding_hash")
