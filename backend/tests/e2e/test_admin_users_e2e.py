import pytest
from httpx import AsyncClient

from tests.e2e.test_setup_e2e import initialize_application


@pytest.mark.asyncio
async def test_admin_user_management_lifecycle_end_to_end(e2e_client: AsyncClient) -> None:
    await initialize_application(e2e_client)

    admin_login_response = await e2e_client.post(
        "/auth/token",
        data={"username": "admin-e2e@example.com", "password": "StrongAdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert admin_login_response.status_code == 200

    admin_token = admin_login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    list_before = await e2e_client.get("/users", headers=auth_headers)
    assert list_before.status_code == 200
    users_before = list_before.json()
    assert any(user["email"] == "admin-e2e@example.com" for user in users_before)

    create_user_response = await e2e_client.post(
        "/users",
        headers=auth_headers,
        json={
            "full_name": "Managed User",
            "email": "managed-e2e@example.com",
            "password": "ManagedPass123!",
            "is_admin": False,
            "is_active": True,
        },
    )
    assert create_user_response.status_code == 201
    managed_user = create_user_response.json()

    disable_user_response = await e2e_client.put(
        f"/users/{managed_user['id']}",
        headers=auth_headers,
        json={"is_active": False},
    )
    assert disable_user_response.status_code == 200
    assert disable_user_response.json()["is_active"] is False

    managed_login_response = await e2e_client.post(
        "/auth/token",
        data={"username": "managed-e2e@example.com", "password": "ManagedPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert managed_login_response.status_code == 401

    delete_user_response = await e2e_client.delete(
        f"/users/{managed_user['id']}",
        headers=auth_headers,
    )
    assert delete_user_response.status_code == 204

    delete_again_response = await e2e_client.delete(
        f"/users/{managed_user['id']}",
        headers=auth_headers,
    )
    assert delete_again_response.status_code == 404

    admin_user_id = next(
        user["id"] for user in users_before if user["email"] == "admin-e2e@example.com"
    )
    self_delete_response = await e2e_client.delete(
        f"/users/{admin_user_id}",
        headers=auth_headers,
    )
    assert self_delete_response.status_code == 400
