from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import email_verification_token as email_verification_crud
from crud.user import create as create_user
from crud.user import get_by_email as get_user_by_email
from i18n.messages import msg
from models.user import User, UserCreate, UserPublic
from services.email_service import SmtpConfig, is_smtp_configured
from services.system_settings import get_system_settings_row
from settings import AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS
from utils.password import get_password_hash
from utils.password_validator import validate_password_strength


async def register_user_handler(
    *,
    session: AsyncSession,
    request: Request,
    user: UserCreate,
    check_rate_limit,
    resolve_auth_backend_base_url,
    generate_email_verification_token,
    email_verification_expiry,
    send_email,
) -> UserPublic:
    check_rate_limit("register", request.client.host if request.client else None, request)

    is_valid, errors = validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors},
        )

    db_user: User | None = await get_user_by_email(
        session=session,
        email=user.email,
    )
    if db_user:
        raise HTTPException(
            status_code=400,
            detail=msg(
                request=request,
                key="auth.email_already_registered",
                default="Email already registered.",
            ),
        )

    settings = await get_system_settings_row(session=session, create_if_missing=False)
    email_enabled = bool(
        settings
        and is_smtp_configured(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_email=settings.smtp_from_email,
        )
    )
    auth_backend_base_url = resolve_auth_backend_base_url(settings)

    try:
        db_user = await create_user(
            session=session,
            full_name=user.full_name,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            email_verified=not email_enabled,
            commit=False,
        )

        if email_enabled:
            plain_token, token_hash = generate_email_verification_token()
            await email_verification_crud.create(
                session=session,
                user_id=db_user.id,
                token_hash=token_hash,
                expires_at=email_verification_expiry(),
                ip=request.client.host if request.client else None,
                commit=False,
            )

            verify_url = f"{auth_backend_base_url}/auth/verify-email?token={plain_token}"
            send_email(
                config=SmtpConfig(
                    host=settings.smtp_host,
                    port=settings.smtp_port,
                    username=settings.smtp_username,
                    password=settings.smtp_password,
                    from_email=settings.smtp_from_email,
                    use_tls=settings.smtp_use_tls,
                ),
                to_email=str(db_user.email),
                subject="Verify your ACE account email",
                body_text=(
                    "Welcome to ACE.\n\n"
                    "Please verify your email by opening this link:\n"
                    f"{verify_url}\n\n"
                    f"The link expires in {AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS} hours."
                ),
            )

        await session.commit()
        await session.refresh(db_user)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to register user: {exc}",
        ) from exc

    return UserPublic(
        id=db_user.id,
        full_name=db_user.full_name,
        email=db_user.email,
        is_active=db_user.is_active,
        is_admin=bool(getattr(db_user, "is_superuser", False)),
        email_verified=db_user.email_verified,
    )
