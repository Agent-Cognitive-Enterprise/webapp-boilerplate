import re

import pytest
from httpx import AsyncClient

import api.auth as auth_api
from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_email_verification_lifecycle_end_to_end(
    e2e_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await initialize_application(e2e_client)

    admin_login = await e2e_client.post(
        "/auth/token",
        data={"username": "admin-e2e@example.com", "password": "StrongAdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    configure_smtp = await e2e_client.put(
        "/admin/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "smtp-pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
            "auth_frontend_base_url": "https://app.custom.example",
            "auth_backend_base_url": "https://api.custom.example",
        },
    )
    assert configure_smtp.status_code == 200
    assert configure_smtp.json()["email_configured"] is True

    sent = {"body": None}

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        sent["body"] = body_text

    monkeypatch.setattr(auth_api, "send_email", _capture_email)

    register_response = await e2e_client.post(
        "/auth/register",
        json={
            "full_name": "Needs Verification",
            "email": "verify-e2e@example.com",
            "password": "NeedsVerify123!",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["email_verified"] is False

    login_before_verify = await e2e_client.post(
        "/auth/token",
        data={"username": "verify-e2e@example.com", "password": "NeedsVerify123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_before_verify.status_code == 403
    assert login_before_verify.json()["detail"] == "Email verification required"

    assert sent["body"] is not None
    assert "https://api.custom.example/auth/verify-email?token=" in str(sent["body"])
    token_match = re.search(r"token=([A-Za-z0-9_\-]+)", sent["body"])
    assert token_match is not None
    verification_token = token_match.group(1)

    verify_response = await e2e_client.get(f"/auth/verify-email?token={verification_token}")
    assert verify_response.status_code == 303
    assert verify_response.headers["location"] == "https://app.custom.example/login"

    login_after_verify = await e2e_client.post(
        "/auth/token",
        data={"username": "verify-e2e@example.com", "password": "NeedsVerify123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_after_verify.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_invalid_token_returns_html_feedback_for_browser(
    e2e_client: AsyncClient,
) -> None:
    await initialize_application(e2e_client)

    response = await e2e_client.get(
        "/auth/verify-email?token=invalid-token",
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    assert "text/html" in response.headers["content-type"]
    assert "Invalid or already used verification token" in response.text
    assert 'id="countdown">10<' in response.text
    assert f'href="{auth_api.AUTH_FRONTEND_BASE_URL}/login"' in response.text
    assert f"const loginUrl = '{auth_api.AUTH_FRONTEND_BASE_URL}/login';" in response.text
