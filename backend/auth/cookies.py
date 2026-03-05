# /backend/auth/cookies.py

from datetime import datetime, timezone
from fastapi import Response

import settings as settings


def set_refresh_cookie(response: Response, token: str, expires_at: datetime):
    # Compute Max-Age from the target expiration
    now = datetime.now(timezone.utc)
    max_age = max(0, int((expires_at - now).total_seconds()))

    # Read settings dynamically so tests or runtime changes take effect
    response.set_cookie(
        key=settings.COOKIE_REFRESH_NAME,
        value=token,
        max_age=max_age,
        expires=expires_at,  # use absolute datetime for Expires
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        secure=bool(settings.COOKIE_SECURE),
        httponly=bool(settings.COOKIE_HTTPONLY),
        samesite=settings.COOKIE_SAME_SITE,
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=settings.COOKIE_REFRESH_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )
