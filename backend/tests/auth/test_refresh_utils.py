# /backend/tests/auth/test_auth_utils.py

import pytest
from datetime import datetime, timedelta, timezone
from starlette.requests import Request as StarletteRequest
from starlette.types import Scope
from fastapi import Request

from auth.refresh_utils import (
    hash_token,
    generate_refresh_token,
    refresh_expiry,
    get_client_ip_ua,
)
from settings import AUTH_REFRESH_TOKEN_EXPIRE_DAYS


def create_request(headers: dict, client_host: str | None) -> Request:
    scope: Scope = {
        "type": "http",
        "headers": [(k.encode("utf-8"), v.encode("utf-8")) for k, v in headers.items()],
        "client": (client_host, 12345) if client_host else None,
    }
    return StarletteRequest(scope)


@pytest.mark.parametrize(
    "token,expected_length",
    [
        ("simple_token", 64),
        ("", 64),
        ("a" * 1000, 64),
        ("special!@#$%^&*()", 64),
    ],
)
def test_hash_token(token: str, expected_length: int):
    # Test hash generation
    hashed = hash_token(token)

    assert isinstance(hashed, str)
    assert len(hashed) == expected_length

    # Test deterministic behavior
    assert hash_token(token) == hash_token(token)

    # Test different inputs produce different hashes
    if token:
        assert hash_token(token) != hash_token(token + "different")


def test_generate_refresh_token():
    plain, token_hash = generate_refresh_token()

    assert isinstance(plain, str)
    assert isinstance(token_hash, str)
    assert len(plain) > 0
    assert len(token_hash) == 64
    assert token_hash == hash_token(plain)


def test_refresh_expiry():
    expiry = refresh_expiry()
    expected = datetime.now(timezone.utc) + timedelta(
        days=AUTH_REFRESH_TOKEN_EXPIRE_DAYS
    )

    assert isinstance(expiry, datetime)

    # Allow a small delta for execution time
    assert abs((expiry - expected).total_seconds()) < 5


def test_get_client_ip_ua():
    # 1. Only x-forwarded-for existing
    req = create_request(
        {"x-forwarded-for": "203.0.113.5", "user-agent": "ua"}, "192.168.1.10"
    )
    ip, ua = get_client_ip_ua(req)

    assert ip == "203.0.113.5"
    assert ua == "ua"

    # 2. No x-forwarded-for, fallback to client.host
    req = create_request({"user-agent": "ua-X"}, "192.0.2.123")
    ip, ua = get_client_ip_ua(req)

    assert ip == "192.0.2.123"
    assert ua == "ua-X"

    # 3. No x-forwarded-for header, no client.host
    req = create_request({"user-agent": "NoClient"}, None)
    ip, ua = get_client_ip_ua(req)

    assert ip is None
    assert ua == "NoClient"

    # 4. Both headers are missing
    req = create_request({}, None)
    ip, ua = get_client_ip_ua(req)

    assert ip is None
    assert ua is None

    # 5. x-forwarded-for is present but empty string, should return empty string not fallback
    req = create_request({"x-forwarded-for": "", "user-agent": "ua"}, "1.2.3.4")
    ip, ua = get_client_ip_ua(req)

    assert ip == ""  # x-forwarded-for header present, even if empty
    assert ua == "ua"

    # 6. x-forwarded-for contains multiple IPs (real world case)
    req = create_request(
        {"x-forwarded-for": "8.8.8.8, 1.2.3.4", "user-agent": "multi-ua"}, "1.2.3.4"
    )
    ip, ua = get_client_ip_ua(req)

    assert ip == "8.8.8.8, 1.2.3.4"
    assert ua == "multi-ua"
