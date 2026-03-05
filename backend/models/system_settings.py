# /backend/models/system_settings.py

from datetime import datetime

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field

from models.base_model import BaseModel


class SystemSettings(BaseModel, table=True):
    __tablename__ = "system_settings"
    __table_args__ = (
        UniqueConstraint("singleton_key", name="uq_system_settings_singleton_key"),
    )

    singleton_key: str = Field(default="default", nullable=False, index=True)

    site_name: str | None = Field(default=None, nullable=True)
    default_locale: str | None = Field(default=None, nullable=True, index=True)
    supported_locales: list[str] = Field(
        default_factory=lambda: ["en"],
        sa_column=Column(JSON, nullable=False),
    )

    allow_registration: bool = Field(default=True, nullable=False)
    app_version: str | None = Field(default=None, nullable=True)

    openai_api_key: str | None = Field(default=None, nullable=True)
    deepseek_api_key: str | None = Field(default=None, nullable=True)
    site_logo: str | None = Field(default=None, nullable=True)
    background_image: str | None = Field(default=None, nullable=True)
    smtp_host: str | None = Field(default=None, nullable=True)
    smtp_port: int | None = Field(default=None, nullable=True)
    smtp_username: str | None = Field(default=None, nullable=True)
    smtp_password: str | None = Field(default=None, nullable=True)
    smtp_from_email: str | None = Field(default=None, nullable=True)
    smtp_use_tls: bool = Field(default=True, nullable=False)
    auth_frontend_base_url: str | None = Field(default=None, nullable=True)
    auth_backend_base_url: str | None = Field(default=None, nullable=True)

    is_initialized: bool = Field(default=False, nullable=False, index=True)
    initialized_at: datetime | None = Field(default=None, nullable=True)
