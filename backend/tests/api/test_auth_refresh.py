import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.refresh_utils import hash_token
from crud.refresh_token import get_by_token_hash, mark_used_and_revoke
from settings import COOKIE_REFRESH_NAME, COOKIE_SESSION_BINDING_NAME
from tests.api.auth_session_test_helpers import (
    TEST_PASSWORD,
    TRUSTED_ORIGIN_HEADERS,
    create_logged_in_user_session,
    extract_cookie_value,
)
from tests.helper import create_test_user


@pytest.mark.asyncio
async def test_refresh_revoked_token(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    refresh_token = (
        await create_logged_in_user_session(client, session)
    ).refresh_token
    client.cookies.set(COOKIE_REFRESH_NAME, refresh_token)

    refresh_token_row = await get_by_token_hash(session, hash_token(refresh_token))
    assert refresh_token_row is not None

    await mark_used_and_revoke(session, refresh_token_row)
    await session.commit()

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_token_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    refresh_token = (
        await create_logged_in_user_session(client, session)
    ).refresh_token
    client.cookies.set(COOKIE_REFRESH_NAME, refresh_token)

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert response.headers.get("set-cookie")


@pytest.mark.asyncio
async def test_refresh_succeeds_across_ip_and_user_agent_changes(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    db_user = await create_test_user(
        session=session,
        password=TEST_PASSWORD,
    )
    response = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": TEST_PASSWORD,
        },
        headers={
            "user-agent": "agent-a",
            "x-forwarded-for": "203.0.113.10",
        },
    )

    assert response.status_code == 200
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        extract_cookie_value(response, COOKIE_REFRESH_NAME),
    )

    mismatch_response = await client.post(
        "/auth/refresh",
        headers={
            **TRUSTED_ORIGIN_HEADERS,
            "user-agent": "agent-b",
            "x-forwarded-for": "198.51.100.21",
        },
    )

    assert mismatch_response.status_code == 200
    assert mismatch_response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_migrates_legacy_token_without_session_binding_hash(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    refresh_token = (
        await create_logged_in_user_session(client, session)
    ).refresh_token

    refresh_token_row = await get_by_token_hash(session, hash_token(refresh_token))
    assert refresh_token_row is not None
    refresh_token_row.client_binding_hash = None
    await session.commit()

    if COOKIE_SESSION_BINDING_NAME in client.cookies:
        client.cookies.delete(COOKIE_SESSION_BINDING_NAME)

    response = await client.post("/auth/refresh", headers=TRUSTED_ORIGIN_HEADERS)

    assert response.status_code == 200
    rotated_refresh_token_row = await get_by_token_hash(
        session,
        hash_token(extract_cookie_value(response, COOKIE_REFRESH_NAME)),
    )
    assert rotated_refresh_token_row is not None
    assert rotated_refresh_token_row.client_binding_hash is not None


@pytest.mark.asyncio
async def test_refresh_token_rotation(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    old_refresh_token = (
        await create_logged_in_user_session(client, session)
    ).refresh_token
    client.cookies.set(COOKIE_REFRESH_NAME, old_refresh_token)

    first_refresh_response = await client.post(
        "/auth/refresh",
        headers=TRUSTED_ORIGIN_HEADERS,
    )

    assert first_refresh_response.status_code == 200
    new_refresh_token = extract_cookie_value(
        first_refresh_response,
        COOKIE_REFRESH_NAME,
    )
    assert new_refresh_token != old_refresh_token

    client.cookies.set(COOKIE_REFRESH_NAME, old_refresh_token)
    replay_response = await client.post(
        "/auth/refresh",
        headers=TRUSTED_ORIGIN_HEADERS,
    )

    assert replay_response.status_code == 401

    client.cookies.set(COOKIE_REFRESH_NAME, new_refresh_token)
    descendant_response = await client.post(
        "/auth/refresh",
        headers=TRUSTED_ORIGIN_HEADERS,
    )

    assert descendant_response.status_code == 401
    assert descendant_response.json()["detail"] == "Invalid refresh token"
