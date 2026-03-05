from http.cookies import SimpleCookie

import pytest
from httpx import AsyncClient

from settings import COOKIE_REFRESH_NAME
from tests.e2e.test_setup_e2e import initialize_application


def extract_refresh_cookie(set_cookie_header: str | None) -> str:
    assert set_cookie_header is not None
    parsed = SimpleCookie()
    parsed.load(set_cookie_header)
    morsel = parsed.get(COOKIE_REFRESH_NAME)
    assert morsel is not None
    return morsel.value


@pytest.mark.asyncio
async def test_refresh_token_rotation_reuse_detection_end_to_end(e2e_client: AsyncClient) -> None:
    await initialize_application(e2e_client)

    register_response = await e2e_client.post(
        "/auth/register",
        json={
            "full_name": "Refresh Security User",
            "email": "refresh-security@example.com",
            "password": "RefreshPass123!",
        },
    )
    assert register_response.status_code == 200

    login_response = await e2e_client.post(
        "/auth/token",
        data={"username": "refresh-security@example.com", "password": "RefreshPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    refresh_token_1 = extract_refresh_cookie(login_response.headers.get("set-cookie"))

    refresh_response = await e2e_client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    refresh_token_2 = extract_refresh_cookie(refresh_response.headers.get("set-cookie"))
    assert refresh_token_2 != refresh_token_1

    # Replay old token: should be rejected and revoke descendants.
    e2e_client.cookies.set(COOKIE_REFRESH_NAME, refresh_token_1)
    replay_response = await e2e_client.post("/auth/refresh")
    assert replay_response.status_code == 401
    assert replay_response.json()["detail"] == "Invalid refresh token"

    # The descendant token should now also be revoked after reuse detection.
    e2e_client.cookies.set(COOKIE_REFRESH_NAME, refresh_token_2)
    descendant_response = await e2e_client.post("/auth/refresh")
    assert descendant_response.status_code == 401
    assert descendant_response.json()["detail"] == "Invalid refresh token"
