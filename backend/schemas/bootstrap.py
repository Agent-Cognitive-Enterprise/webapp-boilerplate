# /backend/schemas/bootstrap.py

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SetupEmailDefaults(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_from_email: EmailStr | None = None
    smtp_use_tls: bool = True
    auth_frontend_base_url: str | None = None
    auth_backend_base_url: str | None = None


class SetupStatusResponse(BaseModel):
    is_initialized: bool
    site_name: str | None = None
    initialized_at: datetime | None = None
    seed_locales: list[str] = Field(default_factory=list)
    email_defaults: SetupEmailDefaults | None = None


class SetupInitializeRequest(BaseModel):
    setup_token: str = Field(min_length=1, max_length=512)
    site_name: str = Field(min_length=1, max_length=120)
    default_locale: str = Field(min_length=2, max_length=16)
    supported_locales: list[str] = Field(min_length=1, max_length=20)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=72)
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=512)
    smtp_from_email: EmailStr | None = None
    smtp_use_tls: bool | None = None
    auth_frontend_base_url: str | None = Field(default=None, max_length=512)
    auth_backend_base_url: str | None = Field(default=None, max_length=512)


class SetupInitializeResponse(BaseModel):
    is_initialized: bool
    site_name: str
    default_locale: str
    supported_locales: list[str]
    admin_email: EmailStr
    email_configured: bool
    initialized_at: datetime
