from __future__ import annotations

import hashlib
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from html import escape
from time import time

from fastapi import HTTPException, Request, status

from i18n.messages import msg
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
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


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


def check_rate_limit(action: str, ip: str | None, request: Request | None = None) -> None:
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
