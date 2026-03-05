# /backend/auth/refresh_utils.py

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import Request

from settings import (
    AUTH_REFRESH_TOKEN_EXPIRE_DAYS,
)


def _hash_token(token: str) -> str:
    """Hashes a token using SHA-256 and returns the hex digest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """
    Generates a secure refresh token and its hash.
    Returns:
        tuple[str, str]: (plain_token, token_hash)
    """
    plain = secrets.token_urlsafe(48)
    return plain, _hash_token(plain)


def refresh_expiry() -> datetime:
    """
    Returns an expiry datetime for the refresh token
    based on AUTH_REFRESH_TOKEN_EXPIRE_DAYS, using UTC.
    """
    return datetime.now(timezone.utc) + timedelta(days=AUTH_REFRESH_TOKEN_EXPIRE_DAYS)


def get_client_ip_ua(request: Request) -> tuple[str | None, str | None]:
    """
    Extracts the client IP address and user-agent string from a FastAPI Request.
    Returns:
        tuple[str | None, str | None]: (ip, user_agent)
    """

    try:
        # Handles possible proxy setups, falling back to direct client IP
        ip = request.headers.get(
            "x-forwarded-for", request.client.host if request.client else None
        )
    except (Exception,):
        ip = None
    ua = request.headers.get("user-agent")

    return ip, ua


# For lookups elsewhere: expose as a non-underscored symbol
hash_token = _hash_token
