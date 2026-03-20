import logging

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.setup_defaults import read_setup_email_defaults_from_env
from api.setup_defaults import resolve_setup_optional_defaults
from i18n.messages import msg
from schemas.admin_settings import EmailSettingsCheckRequest, EmailSettingsCheckResponse
from schemas.bootstrap import SetupInitializeRequest, SetupInitializeResponse, SetupStatusResponse
from services.bootstrap import (
    AlreadyInitializedError,
    BootstrapInput,
    InvalidSetupTokenError,
    SetupMisconfiguredError,
    SetupValidationError,
    get_system_settings,
    initialize_application,
)
from services.email_service import SmtpConfig, is_smtp_configured
from services.ui_label_seed import list_seed_locales

logger = logging.getLogger(__name__)


def send_setup_welcome_email_if_configured(
    *,
    settings,
    admin_email: str,
    send_email,
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
        f"{frontend_base_url}/admin/settings" if frontend_base_url else "/admin/settings"
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


async def get_setup_status_handler(
    session: AsyncSession,
) -> SetupStatusResponse:
    seed_locales = list_seed_locales()
    settings = await get_system_settings(session=session, create_if_missing=False)
    if settings is None:
        return SetupStatusResponse(
            is_initialized=False,
            seed_locales=seed_locales,
            email_defaults=read_setup_email_defaults_from_env(),
        )

    return SetupStatusResponse(
        is_initialized=settings.is_initialized,
        site_name=settings.site_name,
        initialized_at=settings.initialized_at,
        seed_locales=seed_locales,
        email_defaults=None if settings.is_initialized else read_setup_email_defaults_from_env(),
    )


async def setup_page_state_handler(
    request: Request,
    session: AsyncSession,
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


async def run_initial_setup_handler(
    payload: SetupInitializeRequest,
    session: AsyncSession,
    send_email,
) -> SetupInitializeResponse:
    resolved = resolve_setup_optional_defaults(payload)
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
    except SetupMisconfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except InvalidSetupTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except AlreadyInitializedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SetupValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        send_setup_welcome_email_if_configured(
            settings=settings,
            admin_email=admin_user.email,
            send_email=send_email,
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
        initialized_at=settings.initialized_at or settings.created_at,
    )


async def check_setup_email_settings_handler(
    request: Request,
    payload: EmailSettingsCheckRequest,
    test_smtp_connection,
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
