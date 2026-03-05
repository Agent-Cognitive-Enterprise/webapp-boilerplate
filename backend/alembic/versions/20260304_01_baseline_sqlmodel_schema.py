"""baseline sqlmodel schema

Revision ID: 20260304_01
Revises:
Create Date: 2026-03-04 23:59:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260304_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_verification_tokens",
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
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_verification_tokens_id",
        "email_verification_tokens",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_email_verification_tokens_token_hash",
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_email_verification_tokens_user_id",
        "email_verification_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "password_reset_tokens",
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
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_tokens_id", "password_reset_tokens", ["id"], unique=False)
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "refresh_tokens",
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
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("rotated_from_id", sa.CHAR(length=32), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"], unique=False)
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "system_settings",
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
        sa.Column("singleton_key", sa.String(), nullable=False),
        sa.Column("site_name", sa.String(), nullable=True),
        sa.Column("default_locale", sa.String(), nullable=True),
        sa.Column("supported_locales", sa.JSON(), nullable=False),
        sa.Column("allow_registration", sa.Boolean(), nullable=False),
        sa.Column("app_version", sa.String(), nullable=True),
        sa.Column("openai_api_key", sa.String(), nullable=True),
        sa.Column("deepseek_api_key", sa.String(), nullable=True),
        sa.Column("site_logo", sa.String(), nullable=True),
        sa.Column("background_image", sa.String(), nullable=True),
        sa.Column("smtp_host", sa.String(), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True),
        sa.Column("smtp_username", sa.String(), nullable=True),
        sa.Column("smtp_password", sa.String(), nullable=True),
        sa.Column("smtp_from_email", sa.String(), nullable=True),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=False),
        sa.Column("auth_frontend_base_url", sa.String(), nullable=True),
        sa.Column("auth_backend_base_url", sa.String(), nullable=True),
        sa.Column("is_initialized", sa.Boolean(), nullable=False),
        sa.Column("initialized_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("singleton_key", name="uq_system_settings_singleton_key"),
    )
    op.create_index(
        "ix_system_settings_default_locale",
        "system_settings",
        ["default_locale"],
        unique=False,
    )
    op.create_index("ix_system_settings_id", "system_settings", ["id"], unique=False)
    op.create_index(
        "ix_system_settings_is_initialized",
        "system_settings",
        ["is_initialized"],
        unique=False,
    )
    op.create_index(
        "ix_system_settings_singleton_key",
        "system_settings",
        ["singleton_key"],
        unique=False,
    )

    op.create_table(
        "ui_label_suggestions",
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
        sa.Column("label_id", sa.CHAR(length=32), nullable=False),
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ui_label_suggestions_id", "ui_label_suggestions", ["id"], unique=False)
    op.create_index(
        "ix_ui_label_suggestions_label_id",
        "ui_label_suggestions",
        ["label_id"],
        unique=False,
    )
    op.create_index(
        "ix_ui_label_suggestions_user_id",
        "ui_label_suggestions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "ui_labels",
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("locale", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ui_labels_id", "ui_labels", ["id"], unique=False)
    op.create_index("ix_ui_labels_key", "ui_labels", ["key"], unique=False)
    op.create_index("ix_ui_labels_locale", "ui_labels", ["locale"], unique=False)

    op.create_table(
        "ui_locales",
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
        sa.Column("locale", sa.String(), nullable=False),
        sa.Column("values_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ui_locales_id", "ui_locales", ["id"], unique=False)
    op.create_index("ix_ui_locales_locale", "ui_locales", ["locale"], unique=False)

    op.create_table(
        "user_settings",
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
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "route", name="uq_user_route"),
    )
    op.create_index("ix_user_settings_id", "user_settings", ["id"], unique=False)
    op.create_index("ix_user_settings_route", "user_settings", ["route"], unique=False)
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=False)

    op.create_table(
        "users",
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
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_full_name", "users", ["full_name"], unique=False)
    op.create_index("ix_users_id", "users", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_full_name", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_index("ix_user_settings_route", table_name="user_settings")
    op.drop_index("ix_user_settings_id", table_name="user_settings")
    op.drop_table("user_settings")

    op.drop_index("ix_ui_locales_locale", table_name="ui_locales")
    op.drop_index("ix_ui_locales_id", table_name="ui_locales")
    op.drop_table("ui_locales")

    op.drop_index("ix_ui_labels_locale", table_name="ui_labels")
    op.drop_index("ix_ui_labels_key", table_name="ui_labels")
    op.drop_index("ix_ui_labels_id", table_name="ui_labels")
    op.drop_table("ui_labels")

    op.drop_index("ix_ui_label_suggestions_user_id", table_name="ui_label_suggestions")
    op.drop_index("ix_ui_label_suggestions_label_id", table_name="ui_label_suggestions")
    op.drop_index("ix_ui_label_suggestions_id", table_name="ui_label_suggestions")
    op.drop_table("ui_label_suggestions")

    op.drop_index("ix_system_settings_singleton_key", table_name="system_settings")
    op.drop_index("ix_system_settings_is_initialized", table_name="system_settings")
    op.drop_index("ix_system_settings_id", table_name="system_settings")
    op.drop_index("ix_system_settings_default_locale", table_name="system_settings")
    op.drop_table("system_settings")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_email_verification_tokens_user_id", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_token_hash", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
