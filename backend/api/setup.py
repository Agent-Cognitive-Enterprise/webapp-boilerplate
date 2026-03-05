import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.messages import msg
from schemas.admin_settings import EmailSettingsCheckRequest, EmailSettingsCheckResponse
from schemas.bootstrap import (
    SetupEmailDefaults,
    SetupInitializeRequest,
    SetupInitializeResponse,
    SetupStatusResponse,
)
from services.bootstrap import (
    AlreadyInitializedError,
    BootstrapInput,
    InvalidSetupTokenError,
    SetupMisconfiguredError,
    SetupValidationError,
    get_system_settings,
    initialize_application,
)
from services.email_service import (
    SmtpConfig,
    is_smtp_configured,
    send_email,
    test_smtp_connection,
)
from services.ui_label_seed import list_seed_locales
from utils.db import get_session

router = APIRouter()
logger = logging.getLogger(__name__)


def _send_setup_welcome_email_if_configured(
    *,
    settings,
    admin_email: str,
) -> None:
    if not is_smtp_configured(
        host=settings.smtp_host,
        port=settings.smtp_port,
        from_email=settings.smtp_from_email,
    ):
        return

    site_name = settings.site_name or "ACE"
    frontend_base_url = (settings.auth_frontend_base_url or "").rstrip("/")
    admin_settings_url = (
        f"{frontend_base_url}/admin/settings"
        if frontend_base_url
        else "/admin/settings"
    )
    send_email(
        config=SmtpConfig(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
        ),
        to_email=admin_email,
        subject=f"{site_name} is live",
        body_text=(
            f"Hello,\n\n"
            f"Your site '{site_name}' is live now.\n"
            "You can sign in as admin and configure settings here:\n"
            f"{admin_settings_url}\n\n"
            "Thank you,\n"
            "Site Automation\n"
        ),
    )


def _read_setup_email_defaults_from_env() -> SetupEmailDefaults | None:
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
        ]
        + [auth_frontend_base_url, auth_backend_base_url]
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


def _resolve_setup_optional_defaults(payload: SetupInitializeRequest) -> dict[str, object]:
    defaults = _read_setup_email_defaults_from_env()
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


@router.get("/setup/status", response_model=SetupStatusResponse)
async def get_setup_status(
    session: AsyncSession = Depends(get_session),
) -> SetupStatusResponse:
    seed_locales = list_seed_locales()
    settings = await get_system_settings(session=session, create_if_missing=False)
    if settings is None:
        return SetupStatusResponse(
            is_initialized=False,
            seed_locales=seed_locales,
            email_defaults=_read_setup_email_defaults_from_env(),
        )

    return SetupStatusResponse(
        is_initialized=settings.is_initialized,
        site_name=settings.site_name,
        initialized_at=settings.initialized_at,
        seed_locales=seed_locales,
        email_defaults=(
            None
            if settings.is_initialized
            else _read_setup_email_defaults_from_env()
        ),
    )


@router.get("/setup")
async def setup_page_state(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    settings = await get_system_settings(session=session, create_if_missing=False)
    if settings and settings.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=msg(
                request=request,
                key="setup.already_configured",
                default="Application is already configured",
            ),
        )

    return {
        "message": "Application setup required",
        "next": "POST /setup",
    }


@router.post("/setup", response_model=SetupInitializeResponse)
async def run_initial_setup(
    payload: SetupInitializeRequest,
    session: AsyncSession = Depends(get_session),
) -> SetupInitializeResponse:
    resolved = _resolve_setup_optional_defaults(payload)
    try:
        settings, admin_user = await initialize_application(
            session=session,
            data=BootstrapInput(
                setup_token=payload.setup_token,
                site_name=payload.site_name,
                default_locale=payload.default_locale,
                supported_locales=payload.supported_locales,
                admin_email=str(payload.admin_email),
                admin_password=payload.admin_password,
                smtp_host=resolved["smtp_host"],
                smtp_port=resolved["smtp_port"],
                smtp_username=resolved["smtp_username"],
                smtp_password=resolved["smtp_password"],
                smtp_from_email=resolved["smtp_from_email"],
                smtp_use_tls=bool(resolved["smtp_use_tls"]),
                auth_frontend_base_url=resolved["auth_frontend_base_url"],
                auth_backend_base_url=resolved["auth_backend_base_url"],
            ),
        )
    except (SetupMisconfiguredError,) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (InvalidSetupTokenError,) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except (AlreadyInitializedError,) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except (SetupValidationError,) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        _send_setup_welcome_email_if_configured(
            settings=settings,
            admin_email=admin_user.email,
        )
    except Exception:
        logger.exception(
            "Setup completed but failed to send welcome email to admin",
            extra={"admin_email": admin_user.email},
        )

    return SetupInitializeResponse(
        is_initialized=settings.is_initialized,
        site_name=settings.site_name or "",
        default_locale=settings.default_locale or "",
        supported_locales=settings.supported_locales,
        admin_email=admin_user.email,
        email_configured=is_smtp_configured(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_email=settings.smtp_from_email,
        ),
        initialized_at=settings.initialized_at,
    )


@router.post("/setup/email/check", response_model=EmailSettingsCheckResponse)
async def check_setup_email_settings(
    request: Request,
    payload: EmailSettingsCheckRequest,
) -> EmailSettingsCheckResponse:
    host = payload.smtp_host.strip() if payload.smtp_host else None
    username = payload.smtp_username.strip() if payload.smtp_username else None
    from_email = str(payload.smtp_from_email) if payload.smtp_from_email else None

    if not is_smtp_configured(host=host, port=payload.smtp_port, from_email=from_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="common.email_settings_required_fields",
                default="smtp_host, smtp_port and smtp_from_email are required",
            ),
        )

    try:
        test_smtp_connection(
            SmtpConfig(
                host=host,
                port=payload.smtp_port,
                username=username,
                password=payload.smtp_password,
                from_email=from_email,
                use_tls=True if payload.smtp_use_tls is None else payload.smtp_use_tls,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email settings check failed: {exc}",
        ) from exc

    return EmailSettingsCheckResponse(
        success=True,
        message=msg(
            request=request,
            key="common.email_settings_valid",
            default="Email settings are valid",
        ),
    )
