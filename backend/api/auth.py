# /backend/api/auth.py

from datetime import timedelta, datetime, timezone

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from utils.password import get_password_hash, verify_password
from utils.password_validator import validate_password_strength
from auth.cookies import set_refresh_cookie, clear_refresh_cookie
from auth.refresh_utils import (
    generate_refresh_token,
    get_client_ip_ua,
    refresh_expiry,
    hash_token,
)
from crud.refresh_token import (
    create_refresh_token,
    get_by_token_hash,
    mark_used_and_revoke,
    revoke_token_and_descendants,
)
from crud import email_verification_token as email_verification_crud
from models.token import Token
from models.user import User, UserCreate, UserPublic
from settings import (
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS,
    COOKIE_REFRESH_NAME,
)
from services.email_service import SmtpConfig, is_smtp_configured, send_email
from services.system_settings import get_system_settings_row
from utils.db import get_session
from crud.user import get_by_email as get_user_by_email, create as create_user
from utils.helper import to_email_str
from i18n.messages import msg
from api.auth_account_recovery import (
    router as auth_account_recovery_router,
)
from api.auth_shared import (
    _RATE_BUCKETS as SHARED_RATE_BUCKETS,
    check_rate_limit,
    email_verification_expiry,
    generate_email_verification_token,
    resolve_auth_backend_base_url,
)

router = APIRouter()
_RATE_BUCKETS = SHARED_RATE_BUCKETS


@router.post("/auth/register", response_model=UserPublic)
async def register_user(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    user: UserCreate,
):
    check_rate_limit("register", request.client.host if request.client else None, request)

    # Validate password strength
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
        db_user: User = await create_user(
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


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    *,
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    response: Response,
) -> Token:
    check_rate_limit("token", request.client.host if request.client else None, request)

    email = to_email_str(form_data.username)
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.incorrect_credentials",
                default="Incorrect email or password",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.incorrect_credentials",
                default="Incorrect email or password",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg(
                request=request,
                key="auth.email_verification_required",
                default="Email verification required",
            ),
        )

    # Create an access token
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=AUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Create an opaque refresh token and store hash in DB
    plain_rt, rt_hash = generate_refresh_token()
    ip, ua = get_client_ip_ua(request)
    rt = await create_refresh_token(
        session=session,
        user_id=db_user.id,
        token_hash=rt_hash,
        expires_at=refresh_expiry(),
        rotated_from_id=None,
        ip=ip,
        ua=ua,
    )
    await session.commit()

    # Put a plain token into HttpOnly Secure cookie
    set_refresh_cookie(response, plain_rt, rt.expires_at)

    # Return access token (frontend receives access_token); refresh is in the cookie
    return Token(access_token=access_token, refresh_token="", token_type="bearer")


@router.post("/auth/refresh", response_model=Token)
async def rotate_refresh_token(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    response: Response,
) -> Token:
    check_rate_limit("refresh", request.client.host if request.client else None, request)

    # Read refresh token cookie
    plain_rt = request.cookies.get(COOKIE_REFRESH_NAME)
    if not plain_rt:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.refresh_missing",
                default="Missing refresh token",
            ),
        )

    # Lookup by hash
    rt_hash = hash_token(plain_rt)
    rt = await get_by_token_hash(session, rt_hash)
    if not rt:
        # Invalid or reused token -> clear cookie and deny
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.refresh_invalid",
                default="Invalid refresh token",
            ),
        )
    if rt.revoked:
        # Token reuse attempt: revoke descendants as well.
        await revoke_token_and_descendants(session, rt)
        await session.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.refresh_invalid",
                default="Invalid refresh token",
            ),
        )

    current_ip, current_ua = get_client_ip_ua(request)
    if (rt.ip and current_ip and rt.ip != current_ip) or (
        rt.user_agent and current_ua and rt.user_agent != current_ua
    ):
        await revoke_token_and_descendants(session, rt)
        await session.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.refresh_invalid",
                default="Invalid refresh token",
            ),
        )

    # Check expiry
    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        # Expired: revoke and clear cookie
        await mark_used_and_revoke(session, rt)
        await session.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.refresh_expired",
                default="Refresh token expired",
            ),
        )

    # Rotate: mark current as used plus revoked
    await mark_used_and_revoke(session, rt)

    # Create a new refresh token linked to the previous one
    new_plain, new_hash = generate_refresh_token()
    ip, ua = get_client_ip_ua(request)
    new_rt = await create_refresh_token(
        session=session,
        user_id=rt.user_id,
        token_hash=new_hash,
        expires_at=refresh_expiry(),
        rotated_from_id=rt.id,
        ip=ip,
        ua=ua,
    )
    await session.commit()

    # Issue a new access token
    await session.refresh(rt)

    # Lookup user email using rt.user_id
    db_user = await session.get(User, rt.user_id)
    if not db_user:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.user_not_found",
                default="User not found",
            ),
        )
    if not db_user.is_active:
        await revoke_token_and_descendants(session, rt)
        await session.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg(
                request=request,
                key="auth.user_inactive",
                default="User is inactive",
            ),
        )
    if not db_user.email_verified:
        await revoke_token_and_descendants(session, rt)
        await session.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg(
                request=request,
                key="auth.email_verification_required",
                default="Email verification required",
            ),
        )

    access_token = create_access_token({"sub": db_user.email})

    # Set the new refresh token cookie
    set_refresh_cookie(response, new_plain, new_rt.expires_at)

    # Do not return the refresh token in the body; it's set as HttpOnly cookie
    return Token(access_token=access_token, token_type="bearer", refresh_token=None)


@router.post("/auth/logout", status_code=204)
async def logout(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    response: Response,
):
    try:
        plain_rt = request.cookies.get(COOKIE_REFRESH_NAME)
        if plain_rt:
            token_hash = hash_token(plain_rt)
            rt = await get_by_token_hash(session, token_hash)
            if rt:
                await revoke_token_and_descendants(session, rt)
                await session.commit()
    except (Exception,):
        await session.rollback()
    finally:
        clear_refresh_cookie(response)

    response.status_code = 204

    return response
router.include_router(auth_account_recovery_router)
