import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.refresh_utils import hash_token
from crud.refresh_token import get_by_token_hash
from settings import COOKIE_REFRESH_NAME, COOKIE_SESSION_BINDING_NAME
from tests.api.auth_session_test_helpers import (
    TRUSTED_ORIGIN_HEADERS,
    assert_auth_cookie_delete_headers,
    create_logged_in_user_session,
)


@pytest.mark.asyncio
async def test_refresh_missing_cookie_clears_auth_cookies(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing refresh token"
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_refresh_invalid_token_clears_auth_cookies(client: AsyncClient) -> None:
    client.cookies.set(COOKIE_REFRESH_NAME, "notavalidtokenatall")

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_refresh_expired_token_clears_auth_cookies(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    refresh_token = (
        await create_logged_in_user_session(
            client,
            session,
            email="expired-refresh@example.com",
            password="ExpiredRefreshPass123!",
        )
    ).refresh_token

    refresh_token_row = await get_by_token_hash(session, hash_token(refresh_token))
    assert refresh_token_row is not None
    refresh_token_row.expires_at = refresh_token_row.expires_at.replace(year=2000)
    await session.commit()

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token expired"
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_refresh_tampered_session_binding_clears_auth_cookies(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await create_logged_in_user_session(
        client,
        session,
        email="tampered-binding@example.com",
        password="TamperedBindingPass123!",
    )

    client.cookies.set(COOKIE_SESSION_BINDING_NAME, "tampered-session-binding")

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_refresh_inactive_user_clears_auth_cookies(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    logged_in = await create_logged_in_user_session(
        client,
        session,
        email="inactive-refresh@example.com",
        password="InactiveRefreshPass123!",
    )
    logged_in.user.is_active = False
    session.add(logged_in.user)
    await session.commit()

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "User is inactive"
    assert_auth_cookie_delete_headers(response)


@pytest.mark.asyncio
async def test_refresh_unverified_user_clears_auth_cookies(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    logged_in = await create_logged_in_user_session(
        client,
        session,
        email="unverified-refresh@example.com",
        password="UnverifiedRefreshPass123!",
    )
    logged_in.user.email_verified = False
    session.add(logged_in.user)
    await session.commit()

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"
    assert_auth_cookie_delete_headers(response)
