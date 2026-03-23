from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from html import escape

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, col, select

from i18n.messages import msg
from models.auth_rate_limit_event import AuthRateLimitEvent
from settings import (
    AUTH_BACKEND_BASE_URL,
    AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS,
    AUTH_FRONTEND_BASE_URL,
    AUTH_RATE_LIMIT_ENABLED,
)

_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "register": (5, 3600),
    "token": (10, 900),
    "refresh": (30, 3600),
    "forgot_password": (10, 3600),
    "reset_password": (10, 3600),
}


def hash_plain_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()


def generate_email_verification_token() -> tuple[str, str]:
    plain_token = secrets.token_urlsafe(48)
    return plain_token, hash_plain_token(plain_token)


def email_verification_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS)


def normalize_base_url(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    stripped = value.strip().rstrip("/")
    return stripped or fallback


def resolve_auth_frontend_base_url(settings) -> str:
    return normalize_base_url(
        getattr(settings, "auth_frontend_base_url", None) if settings else None,
        AUTH_FRONTEND_BASE_URL,
    )


def resolve_auth_backend_base_url(settings) -> str:
    return normalize_base_url(
        getattr(settings, "auth_backend_base_url", None) if settings else None,
        AUTH_BACKEND_BASE_URL,
    )


async def check_rate_limit(
    *,
    session: AsyncSession,
    action: str,
    ip: str | None,
    request: Request | None = None,
) -> None:
    if not AUTH_RATE_LIMIT_ENABLED:
        return

    limit, window_seconds = _RATE_LIMITS[action]
    key = f"{action}:{ip or 'unknown'}"
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).replace(tzinfo=None)

    await session.execute(
        delete(AuthRateLimitEvent).where(
            and_(
                AuthRateLimitEvent.action == action,
                AuthRateLimitEvent.bucket_key == key,
                col(AuthRateLimitEvent.created_at) < cutoff,
            )
        )
    )

    count_result = await session.execute(
        select(func.count()).select_from(AuthRateLimitEvent).where(
            and_(
                AuthRateLimitEvent.action == action,
                AuthRateLimitEvent.bucket_key == key,
                col(AuthRateLimitEvent.deleted_at).is_(None),
                col(AuthRateLimitEvent.created_at) >= cutoff,
            )
        )
    )
    if int(count_result.scalar_one()) >= limit:
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg(
                request=request,
                key="auth.too_many_requests",
                default="Too many requests. Please try again later.",
            ),
        )

    session.add(AuthRateLimitEvent(action=action, bucket_key=key))
    await session.commit()


def request_accepts_html(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept


def verification_feedback_html(message: str, login_url: str) -> str:
    safe_message = escape(message)
    safe_login_url = escape(login_url, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="10;url={safe_login_url}" />
  <title>Email Verification</title>
</head>
<body>
  <main>
    <h1>Email Verification</h1>
    <p>{safe_message}</p>
    <p>Redirecting to login in 10 seconds. <a href="{safe_login_url}">Go now</a>.</p>
  </main>
</body>
</html>"""
