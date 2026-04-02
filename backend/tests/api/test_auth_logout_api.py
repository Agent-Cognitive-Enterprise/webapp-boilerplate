import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from settings import COOKIE_REFRESH_NAME
from tests.api.auth_session_test_helpers import (
    TRUSTED_ORIGIN_HEADERS,
    assert_auth_cookie_delete_headers,
    create_logged_in_user_session,
)


@pytest.mark.asyncio
async def test_logout_clears_cookie_and_revokes_token(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    refresh_token = (
        await create_logged_in_user_session(client, session)
    ).refresh_token
    client.cookies.set(COOKIE_REFRESH_NAME, refresh_token)

    response = await client.post("/auth/logout", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 204
    assert_auth_cookie_delete_headers(response)

    client.cookies.set(COOKIE_REFRESH_NAME, refresh_token)
    post_logout_refresh = await client.post(
        "/auth/refresh",
        headers=TRUSTED_ORIGIN_HEADERS,
    )

    assert post_logout_refresh.status_code == 401


@pytest.mark.asyncio
async def test_logout_without_cookie_is_idempotent(client: AsyncClient) -> None:
    if COOKIE_REFRESH_NAME in client.cookies:
        client.cookies.clear(COOKIE_REFRESH_NAME)

    response = await client.post("/auth/logout", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 204
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_logout_with_invalid_token_cookie(client: AsyncClient) -> None:
    client.cookies.set(COOKIE_REFRESH_NAME, "notavalidtoken")

    response = await client.post("/auth/logout", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 204
    assert_auth_cookie_delete_headers(response)
