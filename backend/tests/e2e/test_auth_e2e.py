import hashlib

import pytest
from httpx import AsyncClient

import api.auth as auth_api
from settings import COOKIE_REFRESH_NAME
from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_auth_session_lifecycle_end_to_end(e2e_client: AsyncClient) -> None:
    await initialize_application(e2e_client)

    register_response = await e2e_client.post(
        "/auth/register",
        json={
            "full_name": "End To End User",
            "email": "e2e-user@example.com",
            "password": "StrongUserPass123!",
        },
    )
    assert register_response.status_code == 200

    login_response = await e2e_client.post(
        "/auth/token",
        data={"username": "e2e-user@example.com", "password": "StrongUserPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    assert COOKIE_REFRESH_NAME in (login_response.headers.get("set-cookie") or "")

    access_token = login_response.json()["access_token"]
    me_response = await e2e_client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "e2e-user@example.com"

    refresh_response = await e2e_client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]

    logout_response = await e2e_client.post("/auth/logout")
    assert logout_response.status_code == 204

    refresh_after_logout = await e2e_client.post("/auth/refresh")
    assert refresh_after_logout.status_code == 401
    assert refresh_after_logout.json()["detail"] == "Missing refresh token"


@pytest.mark.asyncio
async def test_password_reset_lifecycle_end_to_end(
    e2e_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await initialize_application(e2e_client)

    register_response = await e2e_client.post(
        "/auth/register",
        json={
            "full_name": "Password Reset User",
            "email": "password-reset@example.com",
            "password": "InitialPass123!",
        },
    )
    assert register_response.status_code == 200

    plain_reset_token = "known-reset-token"

    def _deterministic_reset_token() -> tuple[str, str]:
        return plain_reset_token, hashlib.sha256(plain_reset_token.encode()).hexdigest()

    monkeypatch.setattr(auth_api, "generate_reset_token", _deterministic_reset_token)

    forgot_response = await e2e_client.post(
        "/auth/forgot-password",
        json={"email": "password-reset@example.com"},
    )
    assert forgot_response.status_code == 200

    reset_response = await e2e_client.post(
        "/auth/reset-password",
        json={"token": plain_reset_token, "new_password": "UpdatedPass123!"},
    )
    assert reset_response.status_code == 200

    old_password_login = await e2e_client.post(
        "/auth/token",
        data={"username": "password-reset@example.com", "password": "InitialPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert old_password_login.status_code == 401

    new_password_login = await e2e_client.post(
        "/auth/token",
        data={"username": "password-reset@example.com", "password": "UpdatedPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert new_password_login.status_code == 200
