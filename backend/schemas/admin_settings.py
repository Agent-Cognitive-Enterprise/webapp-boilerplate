from pydantic import BaseModel, EmailStr, Field


class AdminSettingsResponse(BaseModel):
    site_name: str | None
    default_locale: str | None
    supported_locales: list[str]
    site_logo: str | None
    background_image: str | None
    openai_api_key_masked: str | None
    deepseek_api_key_masked: str | None
    admin_email: EmailStr
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    smtp_password_masked: str | None
    smtp_from_email: EmailStr | None
    smtp_use_tls: bool
    auth_frontend_base_url: str | None
    auth_backend_base_url: str | None
    email_configured: bool


class AdminSettingsUpdateRequest(BaseModel):
    site_name: str | None = Field(default=None, min_length=1, max_length=120)
    default_locale: str | None = Field(default=None, min_length=2, max_length=16)
    supported_locales: list[str] | None = Field(default=None, min_length=1, max_length=20)
    site_logo: str | None = Field(default=None, max_length=5000000)
    background_image: str | None = Field(default=None, max_length=5000000)
    openai_api_key: str | None = Field(default=None, max_length=512)
    deepseek_api_key: str | None = Field(default=None, max_length=512)
    admin_email: EmailStr | None = None
    admin_password: str | None = Field(default=None, min_length=8, max_length=72)
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=512)
    smtp_from_email: EmailStr | None = None
    smtp_use_tls: bool | None = None
    auth_frontend_base_url: str | None = Field(default=None, max_length=512)
    auth_backend_base_url: str | None = Field(default=None, max_length=512)


class EmailSettingsCheckRequest(BaseModel):
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=512)
    smtp_from_email: EmailStr | None = None
    smtp_use_tls: bool | None = None


class EmailSettingsCheckResponse(BaseModel):
    success: bool
    message: str
