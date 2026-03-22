import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from security.csrf import CSRF_ERROR_DETAIL
from tests.helper import create_test_user


TRUSTED_ORIGIN = "http://localhost:5173"
UNTRUSTED_ORIGIN = "http://evil.example"


async def _login(client: AsyncClient, email: str, password: str) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cookie_authenticated_post_requires_trusted_origin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    password = "CookieAuthPass123!"
    user = await create_test_user(
        session=session,
        email="csrf-cookie@example.com",
        password=password,
    )

    await _login(client, user.email, password)

    response = await client.post(
        "/user-settings",
        json={"route": "/profile", "settings": {"locale": "fr"}},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == CSRF_ERROR_DETAIL


@pytest.mark.asyncio
async def test_cookie_authenticated_post_accepts_trusted_origin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    password = "CookieAuthPass123!"
    user = await create_test_user(
        session=session,
        email="csrf-origin@example.com",
        password=password,
    )

    await _login(client, user.email, password)

    response = await client.post(
        "/user-settings",
        json={"route": "/profile", "settings": {"locale": "fr"}},
        headers={"Origin": TRUSTED_ORIGIN},
    )

    assert response.status_code == 200
    assert response.json()["settings"] == {"locale": "fr"}


@pytest.mark.asyncio
async def test_cookie_authenticated_post_rejects_untrusted_origin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    password = "CookieAuthPass123!"
    user = await create_test_user(
        session=session,
        email="csrf-untrusted@example.com",
        password=password,
    )

    await _login(client, user.email, password)

    response = await client.post(
        "/user-settings",
        json={"route": "/profile", "settings": {"locale": "fr"}},
        headers={"Origin": UNTRUSTED_ORIGIN},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == CSRF_ERROR_DETAIL


@pytest.mark.asyncio
async def test_cookie_authenticated_logout_requires_trusted_origin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    password = "CookieLogoutPass123!"
    user = await create_test_user(
        session=session,
        email="csrf-logout@example.com",
        password=password,
    )

    await _login(client, user.email, password)

    response = await client.post("/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"] == CSRF_ERROR_DETAIL


@pytest.mark.asyncio
async def test_bearer_authenticated_post_does_not_require_origin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = await create_test_user(
        session=session,
        email="csrf-bearer@example.com",
    )
    access_token = create_access_token(data={"sub": user.email})

    response = await client.post(
        "/user-settings",
        json={"route": "/profile", "settings": {"locale": "de"}},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["settings"] == {"locale": "de"}
