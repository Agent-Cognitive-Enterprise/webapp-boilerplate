# /backend/auth/cookies.py

from datetime import datetime, timezone
from typing import Literal, cast

from fastapi import Response

import settings as settings


def set_access_cookie(response: Response, token: str, max_age: int):
    same_site = cast(
        Literal["lax", "strict", "none"] | None,
        settings.COOKIE_SAME_SITE,
    )

    response.set_cookie(
        key=settings.COOKIE_ACCESS_NAME,
        value=token,
        max_age=max_age,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        secure=bool(settings.COOKIE_SECURE),
        httponly=bool(settings.COOKIE_HTTPONLY),
        samesite=same_site,
    )


def set_refresh_cookie(response: Response, token: str, expires_at: datetime):
    # Compute Max-Age from the target expiration
    now = datetime.now(timezone.utc)
    max_age = max(0, int((expires_at - now).total_seconds()))

    same_site = cast(
        Literal["lax", "strict", "none"] | None,
        settings.COOKIE_SAME_SITE,
    )

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
        samesite=same_site,
    )


def clear_access_cookie(response: Response):
    response.delete_cookie(
        key=settings.COOKIE_ACCESS_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=settings.COOKIE_REFRESH_NAME,
        path=settings.COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )
