import pytest
from httpx import AsyncClient

from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_admin_settings_update_lifecycle_end_to_end(e2e_client: AsyncClient) -> None:
    await initialize_application(e2e_client)

    admin_login = await e2e_client.post(
        "/auth/token",
        data={"username": "admin-e2e@example.com", "password": "StrongAdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    initial_settings = await e2e_client.get("/admin/settings", headers=auth_headers)
    assert initial_settings.status_code == 200
    assert initial_settings.json()["admin_email"] == "admin-e2e@example.com"

    update_response = await e2e_client.put(
        "/admin/settings",
        headers=auth_headers,
        json={
            "site_name": "ACE Production E2E",
            "default_locale": "fr",
            "supported_locales": ["fr", "en"],
            "openai_api_key": "sk-openai-e2e-123456",
            "deepseek_api_key": "sk-deepseek-e2e-654321",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "smtp-pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
            "admin_email": "admin-updated@example.com",
            "admin_password": "NewStrongAdminPass123!",
        },
    )
    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["site_name"] == "ACE Production E2E"
    assert updated_payload["default_locale"] == "fr"
    assert updated_payload["supported_locales"] == ["fr", "en"]
    assert updated_payload["admin_email"] == "admin-updated@example.com"
    assert updated_payload["openai_api_key_masked"] is not None
    assert updated_payload["deepseek_api_key_masked"] is not None
    assert updated_payload["smtp_password_masked"] is not None
    assert updated_payload["email_configured"] is True

    health_response = await e2e_client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["app_name"] == "ACE Production E2E"

    old_admin_login = await e2e_client.post(
        "/auth/token",
        data={"username": "admin-e2e@example.com", "password": "StrongAdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert old_admin_login.status_code == 401

    new_admin_login = await e2e_client.post(
        "/auth/token",
        data={"username": "admin-updated@example.com", "password": "NewStrongAdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert new_admin_login.status_code == 200

    refreshed_token = new_admin_login.json()["access_token"]
    refreshed_settings = await e2e_client.get(
        "/admin/settings",
        headers={"Authorization": f"Bearer {refreshed_token}"},
    )
    assert refreshed_settings.status_code == 200
    assert refreshed_settings.json()["admin_email"] == "admin-updated@example.com"
    assert refreshed_settings.json()["email_configured"] is True
