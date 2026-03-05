# /backend/utils/password_reset.py

import secrets
import hashlib
from datetime import datetime, timedelta, UTC


def generate_reset_token() -> tuple[str, str]:
    """
    Generate a secure password reset token.
    Returns: (plain_token, token_hash)
    """
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
    return plain_token, token_hash


def get_reset_token_expiry(hours: int = 1) -> datetime:
    """Get expiry datetime for password reset token (default 1 hour)."""
    return datetime.now(UTC) + timedelta(hours=hours)


def is_token_expired(expires_at: datetime) -> bool:
    """Check if a password reset token has expired."""
    # SQLite-backed rows can be returned as naive datetimes; treat them as UTC.
    normalized_expiry = (
        expires_at.replace(tzinfo=UTC) if expires_at.tzinfo is None else expires_at
    )
    return datetime.now(UTC) > normalized_expiry
