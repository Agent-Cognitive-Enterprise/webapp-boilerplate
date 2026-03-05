import pytest
from httpx import AsyncClient

SETUP_TOKEN = "test-initial-setup-token"


async def initialize_application(client: AsyncClient) -> None:
    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE E2E",
            "default_locale": "en",
            "supported_locales": ["en", "fr"],
            "admin_email": "admin-e2e@example.com",
            "admin_password": "StrongAdminPass123!",
        },
    )
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_setup_and_guard_flow_end_to_end(e2e_client: AsyncClient) -> None:
    status_response = await e2e_client.get("/setup/status")
    assert status_response.status_code == 200
    assert status_response.json()["is_initialized"] is False

    guarded_api_response = await e2e_client.get("/users/me/")
    assert guarded_api_response.status_code == 423
    assert "initialization is required" in guarded_api_response.json()["detail"].lower()

    guarded_html_response = await e2e_client.get(
        "/users/me/",
        headers={"Accept": "text/html"},
    )
    assert guarded_html_response.status_code == 307
    assert guarded_html_response.headers["location"] == "/setup"

    await initialize_application(e2e_client)

    initialized_status_response = await e2e_client.get("/setup/status")
    assert initialized_status_response.status_code == 200
    initialized_payload = initialized_status_response.json()
    assert initialized_payload["is_initialized"] is True
    assert initialized_payload["site_name"] == "ACE E2E"

    setup_page_after_init = await e2e_client.get("/setup")
    assert setup_page_after_init.status_code == 409

    repeated_setup_response = await e2e_client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE E2E CHANGED",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin-2@example.com",
            "admin_password": "AnotherStrongPass123!",
        },
    )
    assert repeated_setup_response.status_code == 409

    status_after_repeated_setup = await e2e_client.get("/setup/status")
    assert status_after_repeated_setup.status_code == 200
    assert status_after_repeated_setup.json()["site_name"] == "ACE E2E"

    health_response = await e2e_client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["app_name"] == "ACE E2E"
