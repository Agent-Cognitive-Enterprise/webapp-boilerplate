import pytest
from httpx import AsyncClient

import api.admin_settings as admin_settings_api
import api.setup as setup_api
from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_setup_email_check_success_and_failure_end_to_end(
    e2e_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_response = await e2e_client.post("/setup/email/check", json={})
    assert missing_response.status_code == 400
    assert "smtp_host, smtp_port and smtp_from_email are required" in (
        missing_response.json()["detail"]
    )

    def _smtp_ok(_config) -> None:
        return None

    monkeypatch.setattr(setup_api, "test_smtp_connection", _smtp_ok)

    success_response = await e2e_client.post(
        "/setup/email/check",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "smtp-pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
        },
    )
    assert success_response.status_code == 200
    assert success_response.json()["success"] is True

    def _smtp_fail(_config) -> None:
        raise RuntimeError("cannot connect")

    monkeypatch.setattr(setup_api, "test_smtp_connection", _smtp_fail)

    failure_response = await e2e_client.post(
        "/setup/email/check",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_from_email": "noreply@example.com",
        },
    )
    assert failure_response.status_code == 400
    assert "Email settings check failed" in failure_response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_email_check_success_and_failure_end_to_end(
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
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    missing_response = await e2e_client.post(
        "/admin/settings/email/check",
        headers=auth_headers,
        json={},
    )
    assert missing_response.status_code == 400
    assert "smtp_host, smtp_port and smtp_from_email are required" in (
        missing_response.json()["detail"]
    )

    def _smtp_ok(_config) -> None:
        return None

    monkeypatch.setattr(admin_settings_api, "test_smtp_connection", _smtp_ok)

    success_response = await e2e_client.post(
        "/admin/settings/email/check",
        headers=auth_headers,
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "smtp-pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
        },
    )
    assert success_response.status_code == 200
    assert success_response.json()["success"] is True

    def _smtp_fail(_config) -> None:
        raise RuntimeError("cannot connect")

    monkeypatch.setattr(admin_settings_api, "test_smtp_connection", _smtp_fail)

    failure_response = await e2e_client.post(
        "/admin/settings/email/check",
        headers=auth_headers,
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_from_email": "noreply@example.com",
        },
    )
    assert failure_response.status_code == 400
    assert "Email settings check failed" in failure_response.json()["detail"]
