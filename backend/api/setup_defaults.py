import os
from typing import TypedDict

from schemas.bootstrap import SetupEmailDefaults, SetupInitializeRequest


class ResolvedSetupDefaults(TypedDict):
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str | None
    smtp_use_tls: bool
    auth_frontend_base_url: str | None
    auth_backend_base_url: str | None


def read_setup_email_defaults_from_env() -> SetupEmailDefaults | None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_raw = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
    smtp_use_tls_raw = os.getenv("SMTP_USE_TLS")
    auth_frontend_base_url = os.getenv("AUTH_FRONTEND_BASE_URL")
    auth_backend_base_url = os.getenv("AUTH_BACKEND_BASE_URL")

    smtp_port: int | None = None
    if smtp_port_raw and smtp_port_raw.strip():
        try:
            smtp_port = int(smtp_port_raw.strip())
        except ValueError:
            smtp_port = None

    smtp_use_tls = True
    if smtp_use_tls_raw and smtp_use_tls_raw.strip():
        smtp_use_tls = smtp_use_tls_raw.strip().lower() in {"1", "true", "yes", "on"}

    has_any_value = any(
        value and value.strip()
        for value in [
            smtp_host,
            smtp_port_raw,
            smtp_username,
            smtp_from_email,
            smtp_use_tls_raw,
            auth_frontend_base_url,
            auth_backend_base_url,
        ]
    )
    if not has_any_value:
        return None

    return SetupEmailDefaults(
        smtp_host=smtp_host.strip() if smtp_host else None,
        smtp_port=smtp_port,
        smtp_username=smtp_username.strip() if smtp_username else None,
        smtp_from_email=smtp_from_email.strip() if smtp_from_email else None,
        smtp_use_tls=smtp_use_tls,
        auth_frontend_base_url=(
            auth_frontend_base_url.strip() if auth_frontend_base_url else None
        ),
        auth_backend_base_url=(
            auth_backend_base_url.strip() if auth_backend_base_url else None
        ),
    )


def resolve_setup_optional_defaults(
    payload: SetupInitializeRequest,
) -> ResolvedSetupDefaults:
    defaults = read_setup_email_defaults_from_env()
    smtp_password_default = os.getenv("SMTP_PASSWORD")

    def _value(payload_value, default_value):
        return payload_value if payload_value is not None else default_value

    smtp_use_tls = (
        payload.smtp_use_tls
        if payload.smtp_use_tls is not None
        else (defaults.smtp_use_tls if defaults is not None else True)
    )
    default_smtp_from_email = (
        str(defaults.smtp_from_email)
        if defaults is not None and defaults.smtp_from_email is not None
        else None
    )

    return {
        "smtp_host": _value(
            payload.smtp_host,
            defaults.smtp_host if defaults is not None else None,
        ),
        "smtp_port": _value(
            payload.smtp_port,
            defaults.smtp_port if defaults is not None else None,
        ),
        "smtp_username": _value(
            payload.smtp_username,
            defaults.smtp_username if defaults is not None else None,
        ),
        "smtp_password": _value(
            payload.smtp_password,
            smtp_password_default if smtp_password_default else None,
        ),
        "smtp_from_email": (
            str(payload.smtp_from_email)
            if payload.smtp_from_email is not None
            else default_smtp_from_email
        ),
        "smtp_use_tls": smtp_use_tls,
        "auth_frontend_base_url": _value(
            payload.auth_frontend_base_url,
            defaults.auth_frontend_base_url if defaults is not None else None,
        ),
        "auth_backend_base_url": _value(
            payload.auth_backend_base_url,
            defaults.auth_backend_base_url if defaults is not None else None,
        ),
    }
