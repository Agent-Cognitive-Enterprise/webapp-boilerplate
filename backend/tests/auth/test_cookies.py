# /backend/auth/cookies.py

from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from fastapi import Response

from auth.cookies import set_refresh_cookie
from settings import (
    COOKIE_REFRESH_NAME,
    COOKIE_SECURE,
    COOKIE_SAME_SITE,
    COOKIE_DOMAIN,
    COOKIE_PATH,
)


def _parse_cookie_from_headers(headers: list[str], name: str):
    """
    Given a list of Set-Cookie header values, parse and return the Morsel
    for the cookie with the provided name, or None if not found.
    """
    for header in headers:
        c = SimpleCookie()
        c.load(header)
        morsel = c.get(name)
        if morsel is not None:
            return morsel
    return None


def test_set_refresh_cookie():
    response = Response()
    token = "test_refresh_token"
    # Use absolute expiry sufficiently far in the future
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    set_refresh_cookie(response, token, expires_at)

    set_cookies = response.headers.getlist("set-cookie")
    assert set_cookies, "No Set-Cookie headers found"

    morsel = _parse_cookie_from_headers(set_cookies, COOKIE_REFRESH_NAME)
    assert morsel is not None, f"Cookie {COOKIE_REFRESH_NAME} not found in headers"

    # value
    assert morsel.value == token, "Refresh token value mismatch"

    # Max-Age: allow a small tolerance because time passes between computing
    # expires_at and the function computing max_age internally.
    parsed_max_age = int(morsel["max-age"])
    expected_max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    # Accept a small drift (e.g., 0-3 seconds)
    assert (
        expected_max_age - 3 <= parsed_max_age <= expected_max_age
    ), f"Max-Age not within tolerance. expected≈{expected_max_age}, got={parsed_max_age}"

    # HttpOnly (check value, not membership in reserved keys)
    assert bool(morsel["httponly"]), "HttpOnly not set in cookie"

    # Secure depends on settings (check value truthiness)
    if COOKIE_SECURE:
        assert bool(morsel["secure"]), "Secure flag expected but not set"
    else:
        assert not bool(morsel["secure"]), "Secure flag not expected in non-secure mode"

    # SameSite exact policy (case-insensitive compare)
    # noinspection SpellCheckingInspection
    assert (
        morsel["samesite"].lower() == str(COOKIE_SAME_SITE).lower()
    ), f"SameSite value mismatch: expected {COOKIE_SAME_SITE}, got {morsel['samesite']}"

    # Path must match settings
    assert morsel["path"] == COOKIE_PATH, f"Path mismatch: expected {COOKIE_PATH}"

    # Domain is optional: only assert if configured
    if COOKIE_DOMAIN:
        assert (
            morsel["domain"] == COOKIE_DOMAIN
        ), f"Domain mismatch: expected {COOKIE_DOMAIN}, got {morsel['domain']}"
