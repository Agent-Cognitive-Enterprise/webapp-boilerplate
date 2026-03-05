from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import get_current_admin_user
from crud.user import get_by_email as get_user_by_email
from models.user import User
from schemas.admin_settings import (
    AdminSettingsResponse,
    AdminSettingsUpdateRequest,
    EmailSettingsCheckRequest,
    EmailSettingsCheckResponse,
)
from services.email_service import SmtpConfig, is_smtp_configured, test_smtp_connection
from services.system_settings import (
    get_system_settings_row,
    masked,
    normalize_locales,
)
from services.ui_label_seed import seed_ui_labels_for_locales
from utils.db import get_session
from utils.password import get_password_hash
from utils.password_validator import validate_password_strength
from i18n.messages import msg


router = APIRouter()


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


@router.get("/admin/settings", response_model=AdminSettingsResponse)
async def get_admin_settings(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdminSettingsResponse:
    settings = await get_system_settings_row(session=session, create_if_missing=True)
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg(
                request=request,
                key="common.settings_missing",
                default="Settings missing",
            ),
        )

    return AdminSettingsResponse(
        site_name=settings.site_name,
        default_locale=settings.default_locale,
        supported_locales=settings.supported_locales or ["en"],
        site_logo=settings.site_logo,
        background_image=settings.background_image,
        openai_api_key_masked=masked(settings.openai_api_key),
        deepseek_api_key_masked=masked(settings.deepseek_api_key),
        admin_email=current_admin.email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password_masked=masked(settings.smtp_password),
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls,
        auth_frontend_base_url=settings.auth_frontend_base_url,
        auth_backend_base_url=settings.auth_backend_base_url,
        email_configured=is_smtp_configured(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_email=settings.smtp_from_email,
        ),
    )


@router.put("/admin/settings", response_model=AdminSettingsResponse)
async def update_admin_settings(
    payload: AdminSettingsUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdminSettingsResponse:
    settings = await get_system_settings_row(session=session, create_if_missing=True)
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg(
                request=request,
                key="common.settings_missing",
                default="Settings missing",
            ),
        )

    if payload.site_name is not None:
        settings.site_name = payload.site_name.strip()

    if payload.site_logo is not None:
        settings.site_logo = _normalize_optional_text(payload.site_logo)

    if payload.background_image is not None:
        settings.background_image = _normalize_optional_text(payload.background_image)

    if payload.openai_api_key is not None:
        settings.openai_api_key = _normalize_optional_text(payload.openai_api_key)

    if payload.deepseek_api_key is not None:
        settings.deepseek_api_key = _normalize_optional_text(payload.deepseek_api_key)

    if payload.smtp_host is not None:
        settings.smtp_host = _normalize_optional_text(payload.smtp_host)

    if payload.smtp_port is not None:
        settings.smtp_port = payload.smtp_port

    if payload.smtp_username is not None:
        settings.smtp_username = _normalize_optional_text(payload.smtp_username)

    if payload.smtp_password is not None:
        settings.smtp_password = _normalize_optional_text(payload.smtp_password)

    if payload.smtp_from_email is not None:
        settings.smtp_from_email = str(payload.smtp_from_email)

    if payload.smtp_use_tls is not None:
        settings.smtp_use_tls = payload.smtp_use_tls

    if payload.auth_frontend_base_url is not None:
        settings.auth_frontend_base_url = _normalize_optional_text(payload.auth_frontend_base_url)

    if payload.auth_backend_base_url is not None:
        settings.auth_backend_base_url = _normalize_optional_text(payload.auth_backend_base_url)

    if payload.default_locale is not None or payload.supported_locales is not None:
        current_default = settings.default_locale or "en"
        current_supported = settings.supported_locales or ["en"]
        target_supported = payload.supported_locales or current_supported
        target_default = payload.default_locale or (
            target_supported[0] if payload.supported_locales is not None else current_default
        )
        normalized_default, normalized_supported = normalize_locales(
            default_locale=target_default,
            supported_locales=target_supported,
        )
        settings.default_locale = normalized_default
        settings.supported_locales = normalized_supported
        await seed_ui_labels_for_locales(
            session=session,
            locales=normalized_supported,
        )

    if payload.admin_email is not None:
        normalized_email = str(payload.admin_email)
        existing_user = await get_user_by_email(session=session, email=payload.admin_email)
        if existing_user and existing_user.id != current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg(
                    request=request,
                    key="admin.admin_email_exists",
                    default="Admin email already exists",
                ),
            )
        current_admin.email = normalized_email
        session.add(current_admin)

    if payload.admin_password is not None:
        is_valid, errors = validate_password_strength(payload.admin_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet security requirements", "errors": errors},
            )
        current_admin.hashed_password = get_password_hash(payload.admin_password)
        session.add(current_admin)

    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    await session.refresh(current_admin)

    return AdminSettingsResponse(
        site_name=settings.site_name,
        default_locale=settings.default_locale,
        supported_locales=settings.supported_locales or ["en"],
        site_logo=settings.site_logo,
        background_image=settings.background_image,
        openai_api_key_masked=masked(settings.openai_api_key),
        deepseek_api_key_masked=masked(settings.deepseek_api_key),
        admin_email=current_admin.email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password_masked=masked(settings.smtp_password),
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls,
        auth_frontend_base_url=settings.auth_frontend_base_url,
        auth_backend_base_url=settings.auth_backend_base_url,
        email_configured=is_smtp_configured(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_email=settings.smtp_from_email,
        ),
    )


@router.post("/admin/settings/email/check", response_model=EmailSettingsCheckResponse)
async def check_admin_email_settings(
    payload: EmailSettingsCheckRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> EmailSettingsCheckResponse:
    settings = await get_system_settings_row(session=session, create_if_missing=True)
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg(
                request=request,
                key="common.settings_missing",
                default="Settings missing",
            ),
        )

    host = _normalize_optional_text(payload.smtp_host) if payload.smtp_host is not None else settings.smtp_host
    port = payload.smtp_port if payload.smtp_port is not None else settings.smtp_port
    username = _normalize_optional_text(payload.smtp_username) if payload.smtp_username is not None else settings.smtp_username
    password = payload.smtp_password if payload.smtp_password is not None else settings.smtp_password
    from_email = str(payload.smtp_from_email) if payload.smtp_from_email is not None else settings.smtp_from_email
    use_tls = payload.smtp_use_tls if payload.smtp_use_tls is not None else settings.smtp_use_tls

    if not is_smtp_configured(host=host, port=port, from_email=from_email):
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
                port=port,
                username=username,
                password=password,
                from_email=from_email,
                use_tls=use_tls,
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
