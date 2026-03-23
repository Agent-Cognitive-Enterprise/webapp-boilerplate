from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from crud import email_verification_token as email_verification_crud
from crud import password_reset_token as password_reset_crud
from crud.refresh_token import revoke_all_for_user
from crud.user import get_by_email as get_user_by_email
from i18n.messages import msg
from models.user import User
from services.email_service import SmtpConfig, is_smtp_configured, send_email
from services.system_settings import get_system_settings_row
from utils.db import get_session
from utils.password import get_password_hash
from utils.password_reset import generate_reset_token, get_reset_token_expiry, is_token_expired
from utils.password_validator import validate_password_strength

from api.auth_shared import (
    check_rate_limit,
    hash_plain_token,
    request_accepts_html,
    resolve_auth_frontend_base_url,
    verification_feedback_html,
)

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.get("/auth/verify-email", status_code=303)
async def verify_email(
    *,
    request: Request,
    session: AsyncSession = Depends(get_session),
    token: str,
):
    settings = await get_system_settings_row(session=session, create_if_missing=False)
    auth_frontend_base_url = resolve_auth_frontend_base_url(settings)
    login_redirect_url = f"{auth_frontend_base_url}/login"
    token_hash = hash_plain_token(token)
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
        if request_accepts_html(request):
            return HTMLResponse(
                content=verification_feedback_html(invalid_or_used_message, login_redirect_url),
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
    await check_rate_limit(
        session=session,
        action="forgot_password",
        ip=request.client.host if request.client else None,
        request=request,
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
    auth_frontend_base_url = resolve_auth_frontend_base_url(settings)

    if db_user:
        await password_reset_crud.invalidate_user_tokens(session, db_user.id)

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

    return {"message": "If that email exists, a password reset link has been sent"}


@router.post("/auth/reset-password", status_code=200)
async def reset_password(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    payload: ResetPasswordRequest,
):
    await check_rate_limit(
        session=session,
        action="reset_password",
        ip=request.client.host if request.client else None,
        request=request,
    )

    token_hash = hash_plain_token(payload.token)
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

    is_valid, errors = validate_password_strength(payload.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors},
        )

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

    db_user.hashed_password = get_password_hash(payload.new_password)
    session.add(db_user)
    await revoke_all_for_user(session, db_user.id)
    await password_reset_crud.mark_as_used(session, reset_token)
    await session.commit()

    return {"message": "Password has been reset successfully"}
