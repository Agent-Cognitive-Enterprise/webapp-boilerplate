from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth.cookies import clear_refresh_cookie, set_refresh_cookie
from auth.refresh_utils import (
    generate_refresh_token,
    get_client_ip_ua,
    hash_token,
    refresh_expiry,
)
from crud.refresh_token import (
    create_refresh_token,
    get_by_token_hash,
    mark_used_and_revoke,
    revoke_token_and_descendants,
)
from crud.user import get_by_email as get_user_by_email
from i18n.messages import msg
from models.token import Token
from models.user import User
from settings import AUTH_ACCESS_TOKEN_EXPIRE_MINUTES, COOKIE_REFRESH_NAME
from utils.helper import to_email_str
from utils.password import verify_password


def _incorrect_credentials_exception(request: Request) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=msg(
            request=request,
            key="auth.incorrect_credentials",
            default="Incorrect email or password",
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def login_for_access_token_handler(
    *,
    session: AsyncSession,
    form_data: OAuth2PasswordRequestForm,
    request: Request,
    response: Response,
    check_rate_limit,
    create_access_token,
) -> Token:
    check_rate_limit("token", request.client.host if request.client else None, request)

    email = to_email_str(form_data.username)
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise _incorrect_credentials_exception(request)
    if not db_user.is_active:
        raise _incorrect_credentials_exception(request)
    if not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg(
                request=request,
                key="auth.email_verification_required",
                default="Email verification required",
            ),
        )

    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=AUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
    )

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

    set_refresh_cookie(response, plain_rt, rt.expires_at)

    return Token(access_token=access_token, refresh_token="", token_type="bearer")


async def rotate_refresh_token_handler(
    *,
    session: AsyncSession,
    request: Request,
    response: Response,
    check_rate_limit,
    create_access_token,
) -> Token:
    check_rate_limit("refresh", request.client.host if request.client else None, request)

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

    rt_hash = hash_token(plain_rt)
    rt = await get_by_token_hash(session, rt_hash)
    if not rt:
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

    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
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

    await mark_used_and_revoke(session, rt)

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

    await session.refresh(rt)
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
    set_refresh_cookie(response, new_plain, new_rt.expires_at)

    return Token(access_token=access_token, token_type="bearer", refresh_token=None)


async def logout_handler(
    *,
    session: AsyncSession,
    request: Request,
    response: Response,
) -> Response:
    try:
        plain_rt = request.cookies.get(COOKIE_REFRESH_NAME)
        if plain_rt:
            token_hash = hash_token(plain_rt)
            rt = await get_by_token_hash(session, token_hash)
            if rt:
                await revoke_token_and_descendants(session, rt)
                await session.commit()
    except Exception:
        await session.rollback()
    finally:
        clear_refresh_cookie(response)

    response.status_code = 204
    return response
