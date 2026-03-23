"""add auth rate limit events

Revision ID: 20260323_02
Revises: 20260323_01
Create Date: 2026-03-23 00:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260323_02"
down_revision: Union[str, None] = "20260323_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_rate_limit_events",
        sa.Column("id", sa.CHAR(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("bucket_key", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_rate_limit_events_action",
        "auth_rate_limit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_bucket_key",
        "auth_rate_limit_events",
        ["bucket_key"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_id",
        "auth_rate_limit_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_rate_limit_events_action_bucket_created_at",
        "auth_rate_limit_events",
        ["action", "bucket_key", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_rate_limit_events_action_bucket_created_at",
        table_name="auth_rate_limit_events",
    )
    op.drop_index("ix_auth_rate_limit_events_id", table_name="auth_rate_limit_events")
    op.drop_index("ix_auth_rate_limit_events_bucket_key", table_name="auth_rate_limit_events")
    op.drop_index("ix_auth_rate_limit_events_action", table_name="auth_rate_limit_events")
    op.drop_table("auth_rate_limit_events")
