import uuid

import pytest
from httpx import AsyncClient

from crud.user_settings import count_user_settings, get_user_settings
from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_user_settings_lifecycle_end_to_end(
    e2e_client: AsyncClient,
    e2e_db_session,
) -> None:
    await initialize_application(e2e_client)

    unauthorized_response = await e2e_client.post(
        "/user-settings",
        json={"route": "/dashboard", "settings": {"collapsed": True}},
    )
    assert unauthorized_response.status_code == 401
    assert unauthorized_response.json()["detail"] == "Not authenticated"

    register_response = await e2e_client.post(
        "/auth/register",
        json={
            "full_name": "User Settings E2E",
            "email": "user-settings-e2e@example.com",
            "password": "UserSettingsPass123!",
        },
    )
    assert register_response.status_code == 200

    login_response = await e2e_client.post(
        "/auth/token",
        data={
            "username": "user-settings-e2e@example.com",
            "password": "UserSettingsPass123!",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    me_response = await e2e_client.get("/users/me/", headers=auth_headers)
    assert me_response.status_code == 200
    user_id = uuid.UUID(me_response.json()["id"])

    route = "/dashboard"
    initial_settings = {"collapsed": True, "density": "comfortable"}

    save_response = await e2e_client.post(
        "/user-settings",
        json={"route": route, "settings": initial_settings},
        headers=auth_headers,
    )
    assert save_response.status_code == 200
    assert save_response.json()["route"] == route
    assert save_response.json()["settings"] == initial_settings

    fetch_response = await e2e_client.post(
        "/user-settings",
        json={"route": route, "settings": None},
        headers=auth_headers,
    )
    assert fetch_response.status_code == 200
    assert fetch_response.json()["settings"] == initial_settings

    updated_settings = {"collapsed": False, "density": "compact"}
    update_response = await e2e_client.post(
        "/user-settings",
        json={"route": route, "settings": updated_settings},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["settings"] == updated_settings

    refreshed_response = await e2e_client.post(
        "/user-settings",
        json={"route": route, "settings": None},
        headers=auth_headers,
    )
    assert refreshed_response.status_code == 200
    assert refreshed_response.json()["settings"] == updated_settings

    stored_settings = await get_user_settings(
        session=e2e_db_session,
        user_id=user_id,
        route=route,
    )
    assert stored_settings is not None
    assert stored_settings.settings == updated_settings
    assert await count_user_settings(
        session=e2e_db_session,
        user_id=user_id,
        route=route,
    ) == 1
