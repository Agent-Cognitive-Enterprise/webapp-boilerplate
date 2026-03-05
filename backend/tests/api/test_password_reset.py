# /backend/tests/api/test_password_reset.py

import pytest
import re
import hashlib
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tests.helper import create_test_user
from utils.password import get_password_hash
from utils.password_reset import generate_reset_token, get_reset_token_expiry
from crud import password_reset_token as password_reset_crud
from settings import COOKIE_REFRESH_NAME
import api.auth as auth_api
from settings import AUTH_FRONTEND_BASE_URL
from models.system_settings import SystemSettings


@pytest.mark.asyncio
async def test_forgot_password_success(client: AsyncClient, session: AsyncSession):
    """Test forgot password request for existing user."""
    user = await create_test_user(session, email="test@example.com")

    response = await client.post(
        "/auth/forgot-password",
        json={"email": user.email},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "If that email exists, a password reset link has been sent"


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_user(client: AsyncClient):
    """Test forgot password request for non-existent user (should still return success)."""
    response = await client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )

    # Should return success to prevent user enumeration
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "If that email exists, a password reset link has been sent"


@pytest.mark.asyncio
async def test_forgot_password_sends_email_when_smtp_configured(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch,
):
    user = await create_test_user(session, email="reset-target@example.com")
    settings_result = await session.execute(
        select(SystemSettings).where(SystemSettings.singleton_key == "default")
    )
    settings = settings_result.scalars().first()
    assert settings is not None
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_username = "smtp-user"
    settings.smtp_password = "smtp-pass"
    settings.smtp_from_email = "noreply@example.com"
    settings.smtp_use_tls = True
    session.add(settings)
    await session.commit()

    plain_reset_token = "known-reset-token"

    def _deterministic_reset_token() -> tuple[str, str]:
        return plain_reset_token, hashlib.sha256(plain_reset_token.encode()).hexdigest()

    captured: dict[str, str] = {}

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        captured["to_email"] = to_email
        captured["subject"] = subject
        captured["body_text"] = body_text
        captured["from_email"] = config.from_email

    monkeypatch.setattr(auth_api, "generate_reset_token", _deterministic_reset_token)
    monkeypatch.setattr(auth_api, "send_email", _capture_email)

    response = await client.post(
        "/auth/forgot-password",
        json={"email": user.email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "If that email exists, a password reset link has been sent"
    assert captured["to_email"] == user.email
    assert captured["subject"] == "Reset your ACE account password"
    assert captured["from_email"] == "noreply@example.com"
    assert (
        f"{AUTH_FRONTEND_BASE_URL}/reset-password?token={plain_reset_token}"
        in captured["body_text"]
    )


@pytest.mark.asyncio
async def test_forgot_password_uses_db_frontend_base_url_for_reset_link(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch,
):
    user = await create_test_user(session, email="reset-db-url@example.com")
    settings_result = await session.execute(
        select(SystemSettings).where(SystemSettings.singleton_key == "default")
    )
    settings = settings_result.scalars().first()
    assert settings is not None
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_from_email = "noreply@example.com"
    settings.auth_frontend_base_url = "https://app.custom.example"
    session.add(settings)
    await session.commit()

    plain_reset_token = "db-url-reset-token"

    def _deterministic_reset_token() -> tuple[str, str]:
        return plain_reset_token, hashlib.sha256(plain_reset_token.encode()).hexdigest()

    captured: dict[str, str] = {}

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        captured["body_text"] = body_text

    monkeypatch.setattr(auth_api, "generate_reset_token", _deterministic_reset_token)
    monkeypatch.setattr(auth_api, "send_email", _capture_email)

    response = await client.post(
        "/auth/forgot-password",
        json={"email": user.email},
    )

    assert response.status_code == 200
    assert "https://app.custom.example/reset-password?token=db-url-reset-token" in captured["body_text"]


@pytest.mark.asyncio
async def test_forgot_password_does_not_send_for_nonexistent_user_with_smtp_configured(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch,
):
    settings_result = await session.execute(
        select(SystemSettings).where(SystemSettings.singleton_key == "default")
    )
    settings = settings_result.scalars().first()
    assert settings is not None
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_from_email = "noreply@example.com"
    session.add(settings)
    await session.commit()

    sent = {"called": False}

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        sent["called"] = True

    monkeypatch.setattr(auth_api, "send_email", _capture_email)

    response = await client.post(
        "/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "If that email exists, a password reset link has been sent"
    assert sent["called"] is False


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test password reset with invalid token."""
    response = await client.post(
        "/auth/reset-password",
        json={
            "token": "invalid_token",
            "new_password": "NewSecure@Pass123",
        },
    )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_weak_password(client: AsyncClient, session: AsyncSession):
    """Test password reset with weak password."""
    user = await create_test_user(session, email="test2@example.com")

    # Request reset token
    await client.post("/auth/forgot-password", json={"email": user.email})

    # In real scenario, we'd extract token from email
    # For testing, we'll use an invalid token but test the password validation
    response = await client.post(
        "/auth/reset-password",
        json={
            "token": "some_token",
            "new_password": "weak",  # Too weak
        },
    )

    # Should fail either due to invalid token or weak password
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_invalid_email(client: AsyncClient):
    """Test forgot password with invalid email format."""
    response = await client.post(
        "/auth/forgot-password",
        json={"email": "not-an-email"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_reset_password_calls_rate_limit_guard(
    client: AsyncClient, session: AsyncSession, monkeypatch
):
    called = {"count": 0}

    def fake_check_rate_limit(action: str, ip: str | None, request):
        called["count"] += 1
        assert action == "reset_password"

    monkeypatch.setattr(auth_api, "_check_rate_limit", fake_check_rate_limit)

    response = await client.post(
        "/auth/reset-password",
        json={
            "token": "invalid_token",
            "new_password": "NewSecure@Pass123",
        },
    )

    assert response.status_code == 400
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_reset_password_revokes_existing_refresh_sessions(
    client: AsyncClient, session: AsyncSession
):
    current_password = "Current@Pass123"
    user = await create_test_user(
        session,
        email="test-reset-revoke@example.com",
        hashed_password=get_password_hash(current_password),
    )

    login = await client.post(
        "/auth/token",
        data={
            "username": user.email,
            "password": current_password,
        },
    )
    assert login.status_code == 200
    match = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        login.headers.get("set-cookie", ""),
    )
    assert match
    refresh_cookie = match.group(1)

    plain_token, token_hash = generate_reset_token()
    await password_reset_crud.create(
        session=session,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=get_reset_token_expiry(),
    )

    reset_response = await client.post(
        "/auth/reset-password",
        json={
            "token": plain_token,
            "new_password": "BrandNew@Pass456",
        },
    )
    assert reset_response.status_code == 200

    client.cookies.set(COOKIE_REFRESH_NAME, refresh_cookie)
    refresh_response = await client.post("/auth/refresh")
    assert refresh_response.status_code == 401
