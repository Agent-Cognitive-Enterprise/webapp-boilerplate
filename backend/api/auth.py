# /backend/api/auth.py

from datetime import timedelta, datetime, timezone
import hashlib
import secrets
from html import escape
from collections import defaultdict, deque
from time import time
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
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
    revoke_all_for_user,
    revoke_token_and_descendants,
)
from crud import password_reset_token as password_reset_crud
from crud import email_verification_token as email_verification_crud
from models.token import Token
from models.user import User, UserCreate, UserPublic
from settings import (
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_BACKEND_BASE_URL,
    AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS,
    AUTH_FRONTEND_BASE_URL,
    COOKIE_REFRESH_NAME,
)
from settings import AUTH_RATE_LIMIT_ENABLED
from services.email_service import SmtpConfig, is_smtp_configured, send_email
from services.system_settings import get_system_settings_row
from utils.db import get_session
from crud.user import get_by_email as get_user_by_email, create as create_user
from utils.helper import to_email_str
from utils.password_reset import (
    generate_reset_token,
    get_reset_token_expiry,
    is_token_expired,
)
from pydantic import BaseModel, EmailStr
from i18n.messages import msg

router = APIRouter()

_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "register": (5, 3600),
    "token": (10, 900),
    "refresh": (30, 3600),
    "forgot_password": (10, 3600),
    "reset_password": (10, 3600),
}
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def _hash_plain_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()


def _generate_email_verification_token() -> tuple[str, str]:
    plain_token = secrets.token_urlsafe(48)
    return plain_token, _hash_plain_token(plain_token)


def _email_verification_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS)


def _normalize_base_url(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    stripped = value.strip().rstrip("/")
    return stripped or fallback


def _resolve_auth_frontend_base_url(settings) -> str:
    return _normalize_base_url(
        getattr(settings, "auth_frontend_base_url", None) if settings else None,
        AUTH_FRONTEND_BASE_URL,
    )


def _resolve_auth_backend_base_url(settings) -> str:
    return _normalize_base_url(
        getattr(settings, "auth_backend_base_url", None) if settings else None,
        AUTH_BACKEND_BASE_URL,
    )


def _check_rate_limit(action: str, ip: str | None, request: Request | None = None) -> None:
    if not AUTH_RATE_LIMIT_ENABLED:
        return
    limit, window_seconds = _RATE_LIMITS[action]
    key = f"{action}:{ip or 'unknown'}"
    now = time()
    bucket = _RATE_BUCKETS[key]
    cutoff = now - window_seconds

    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg(
                request=request,
                key="auth.too_many_requests",
                default="Too many requests. Please try again later.",
            ),
        )

    bucket.append(now)


@router.post("/auth/register", response_model=UserPublic)
async def register_user(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    user: UserCreate,
):
    _check_rate_limit("register", request.client.host if request.client else None, request)

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
    auth_backend_base_url = _resolve_auth_backend_base_url(settings)

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
            plain_token, token_hash = _generate_email_verification_token()
            await email_verification_crud.create(
                session=session,
                user_id=db_user.id,
                token_hash=token_hash,
                expires_at=_email_verification_expiry(),
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
    _check_rate_limit("token", request.client.host if request.client else None, request)

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
    _check_rate_limit("refresh", request.client.host if request.client else None, request)

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


# TODO: Implement tests for this endpoint
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
            token_hash = hash_token(plain_rt)  # ensure this is defined/imported
            rt = await get_by_token_hash(session, token_hash)
            if rt:
                await revoke_token_and_descendants(session, rt)
                await session.commit()
    except (Exception,):
        # Optional: log the error
        await session.rollback()
    finally:
        # Always clear the cookie on the same response object
        clear_refresh_cookie(response)

    # Either rely on the decorator's status_code or set it explicitly:
    response.status_code = 204

    return response


# Pydantic models for password reset requests
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def _request_accepts_html(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept


def _verification_feedback_html(message: str, login_url: str) -> str:
    safe_message = escape(message)
    safe_login_url = escape(login_url, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="10;url={safe_login_url}" />
  <title>Email Verification</title>
  <style>
    :root {{
      color-scheme: light;
      --bg-top: #eef2ff;
      --bg-bottom: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --subtle: #475569;
      --border: #dbe3f3;
      --shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: linear-gradient(160deg, var(--bg-top), var(--bg-bottom));
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--text);
      padding: 1rem;
    }}
    .card {{
      width: min(640px, 100%);
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 2rem 1.5rem;
      text-align: center;
    }}
    h1 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
    }}
    p.message {{
      margin: 1rem 0 0;
      font-size: 1.05rem;
      color: var(--subtle);
    }}
    p.redirect {{
      margin: 1.25rem 0 0;
      font-size: 0.95rem;
      color: var(--subtle);
    }}
    a {{
      color: #1d4ed8;
      text-decoration: none;
      font-weight: 600;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1>Email Verification</h1>
    <p class="message">{safe_message}</p>
    <p class="redirect">Redirecting to login in <span id="countdown">10</span> seconds. <a href="{safe_login_url}">Go now</a>.</p>
  </main>
  <script>
    let remaining = 10;
    const countdown = document.getElementById("countdown");
    const loginUrl = {safe_login_url!r};
    const timer = setInterval(() => {{
      remaining -= 1;
      if (countdown) countdown.textContent = String(Math.max(remaining, 0));
      if (remaining <= 0) {{
        clearInterval(timer);
        window.location.replace(loginUrl);
      }}
    }}, 1000);
  </script>
</body>
</html>"""


@router.get("/auth/verify-email", status_code=303)
async def verify_email(
    *,
    request: Request,
    session: AsyncSession = Depends(get_session),
    token: str,
):
    settings = await get_system_settings_row(session=session, create_if_missing=False)
    auth_frontend_base_url = _resolve_auth_frontend_base_url(settings)
    login_redirect_url = f"{auth_frontend_base_url}/login"
    token_hash = _hash_plain_token(token)
    verification_token = await email_verification_crud.get_by_token_hash(
        session=session,
        token_hash=token_hash,
    )

    if not verification_token or verification_token.used:
        invalid_or_used_message = msg(
            request=request,
            key="auth.verify_token_invalid_or_used",
            default="Invalid or already used verification token",
        )
        if _request_accepts_html(request):
            return HTMLResponse(
                content=_verification_feedback_html(invalid_or_used_message, login_redirect_url),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=invalid_or_used_message,
        )

    if is_token_expired(verification_token.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="auth.verify_token_expired",
                default="Verification token has expired",
            ),
        )

    db_user = await session.get(User, verification_token.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg(
                request=request,
                key="auth.user_not_found",
                default="User not found",
            ),
        )

    db_user.email_verified = True
    session.add(db_user)
    await email_verification_crud.mark_as_used(
        session=session,
        token=verification_token,
        commit=False,
    )
    await email_verification_crud.invalidate_user_tokens(
        session=session,
        user_id=db_user.id,
        commit=False,
    )
    await session.commit()

    return RedirectResponse(url=login_redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/auth/forgot-password", status_code=200)
async def forgot_password(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    payload: ForgotPasswordRequest,
):
    """
    Request a password reset. Always returns success to prevent user enumeration.
    If user exists and SMTP is configured, a reset token is generated and emailed.
    """
    _check_rate_limit(
        "forgot_password",
        request.client.host if request.client else None,
        request,
    )

    db_user = await get_user_by_email(session, payload.email)

    settings = await get_system_settings_row(session=session, create_if_missing=False)
    email_enabled = bool(
        settings
        and is_smtp_configured(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_email=settings.smtp_from_email,
        )
    )
    auth_frontend_base_url = _resolve_auth_frontend_base_url(settings)

    if db_user:
        # Invalidate any existing reset tokens for this user
        await password_reset_crud.invalidate_user_tokens(session, db_user.id)

        # Generate new reset token
        plain_token, token_hash = generate_reset_token()
        ip = request.client.host if request.client else None

        await password_reset_crud.create(
            session=session,
            user_id=db_user.id,
            token_hash=token_hash,
            expires_at=get_reset_token_expiry(),
            ip=ip,
        )

        if email_enabled:
            reset_url = f"{auth_frontend_base_url}/reset-password?token={plain_token}"
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
                subject="Reset your ACE account password",
                body_text=(
                    "We received a request to reset your ACE account password.\n\n"
                    "Open this link to choose a new password:\n"
                    f"{reset_url}\n\n"
                    "If you did not request this change, you can ignore this email."
                ),
            )

    # Always return success to prevent user enumeration
    return {"message": "If that email exists, a password reset link has been sent"}


@router.post("/auth/reset-password", status_code=200)
async def reset_password(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    payload: ResetPasswordRequest,
):
    """
    Reset password using a valid reset token.
    """
    _check_rate_limit("reset_password", request.client.host if request.client else None, request)

    # Hash the provided token to look it up
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()

    # Find the reset token
    reset_token = await password_reset_crud.get_by_token_hash(session, token_hash)

    if not reset_token or reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="auth.reset_token_invalid_or_used",
                default="Invalid or already used reset token",
            ),
        )

    if is_token_expired(reset_token.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="auth.reset_token_expired",
                default="Reset token has expired",
            ),
        )

    # Validate new password strength
    is_valid, errors = validate_password_strength(payload.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors},
        )

    # Get the user
    db_user = await session.get(User, reset_token.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg(
                request=request,
                key="auth.user_not_found",
                default="User not found",
            ),
        )

    # Update password
    db_user.hashed_password = get_password_hash(payload.new_password)
    session.add(db_user)

    # Revoke all active refresh sessions after password reset.
    await revoke_all_for_user(session, db_user.id)

    # Mark token as used
    await password_reset_crud.mark_as_used(session, reset_token)

    await session.commit()

    return {"message": "Password has been reset successfully"}
