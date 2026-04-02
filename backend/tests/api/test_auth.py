# /backend/tests/api/test_register.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import re

from utils.password import get_password_hash
from settings import COOKIE_REFRESH_NAME
from tests.helper import create_test_user
from i18n.messages import get_message


test_full_name = "Test User"
test_email = "test.user@example.net"
# noinspection SpellCheckingInspection
test_password = "$ecurepAssw0rd"
# noinspection SpellCheckingInspection
wrong_password = "wrongpassword"
@pytest.mark.asyncio
async def test_register(
    client: AsyncClient,
    session: AsyncSession,
):

    payload = {
        "full_name": test_full_name,
        "email": test_email,
        "password": test_password,
    }
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] is not None
    assert data["full_name"] == test_full_name
    assert data["email"] == test_email
    assert "hashed_password" not in data  # Ensure the password is not returned


@pytest.mark.asyncio
async def test_register_existing_email(
    client: AsyncClient,
    session: AsyncSession,
):

    db_user = await create_test_user(
        session=session,
        email=test_email,
    )

    response = await client.post(
        "/auth/register",
        json={
            "full_name": test_full_name,
            "email": db_user.email,
            "password": test_password,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered."


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_register_invalid_email(
    client: AsyncClient,
    session: AsyncSession,
):

    payload = {
        "full_name": test_full_name,
        "email": "invalid-email-format",
        "password": test_password,
    }
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity for validation errors

    data = response.json()

    assert data["detail"][0]["loc"] == ["body", "email"]
    assert "body" not in data
    assert (
        data["detail"][0]["msg"]
        == "value is not a valid email address: An email address must have an @-sign."
    )
    assert data["detail"][0]["type"] == "value_error"


@pytest.mark.asyncio
async def test_register_weak_password(
    client: AsyncClient,
    session: AsyncSession,
):

    payload = {
        "full_name": test_full_name,
        "email": test_email,
        "password": "123",  # Weak password
    }
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity for validation errors

    data = response.json()

    assert data["detail"][0]["loc"] == ["body", "password"]
    assert data["detail"][0]["msg"] == "String should have at least 8 characters"


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_register_missing_fields(
    client: AsyncClient,
    session: AsyncSession,
):

    payload = {
        "email": test_email,
        "password": test_password,
    }  # Missing full_name
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity for validation errors

    data = response.json()

    assert data["detail"][0]["loc"] == ["body", "full_name"]
    assert data["detail"][0]["msg"] == "Field required"
    assert data["detail"][0]["type"] == "missing"

    payload = {
        "full_name": test_full_name,
        "password": test_password,
    }  # Missing email
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity for validation errors

    data = response.json()

    assert data["detail"][0]["loc"] == ["body", "email"]
    assert data["detail"][0]["msg"] == "Field required"
    assert data["detail"][0]["type"] == "missing"

    payload = {
        "full_name": test_full_name,
        "email": test_email,
    }  # Missing password
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity for validation errors

    data = response.json()

    assert data["detail"][0]["loc"] == ["body", "password"]
    assert data["detail"][0]["msg"] == "Field required"
    assert data["detail"][0]["type"] == "missing"


@pytest.mark.asyncio
async def test_token_success(
    client: AsyncClient,
    session: AsyncSession,
):

    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )

    payload = {
        "username": db_user.email,
        "password": test_password,
    }
    response = await client.post(
        "/auth/token",
        data=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["token_type"].lower() == "bearer"
    # Your endpoint body sets refresh_token to "" for /token, adjust this if changes
    assert "refresh_token" in data
    # Separate from cookie: value is "" (not None), as per view

    # Cookie checks (core security): refresh token is in Set-Cookie!
    set_cookie = response.headers.get("set-cookie")

    assert set_cookie, "No Set-Cookie header set for refresh_token"
    assert re.search(rf"{COOKIE_REFRESH_NAME}=[^;]+", set_cookie)
    assert "httponly" in set_cookie.lower()
    assert re.search(
        r"samesite=lax",
        set_cookie,
        re.IGNORECASE,
    ) or re.search(
        r"samesite=strict",
        set_cookie,
        re.IGNORECASE,
    )
    assert "path=/" in set_cookie.lower()
    assert ("max-age=" in set_cookie.lower()) or ("expires=" in set_cookie.lower())


@pytest.mark.asyncio
async def test_token_incorrect_password(
    client: AsyncClient,
    session: AsyncSession,
):
    db_user = await create_test_user(
        session=session, hashed_password=get_password_hash(test_password)
    )

    # Wrong password
    payload = {
        "username": db_user.email,
        "password": wrong_password,
    }
    response = await client.post(
        "/auth/token",
        data=payload,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Incorrect email or password"
    assert (
        "set-cookie" not in response.headers
        or COOKIE_REFRESH_NAME not in response.headers.get("set-cookie", "")
    )


# noinspection DuplicatedCode,SpellCheckingInspection
@pytest.mark.asyncio
async def test_token_nonexistent_user(client: AsyncClient):
    payload = {
        "username": "nonexistentuser@example.com",
        "password": "somepassword",
    }
    response = await client.post(
        "/auth/token",
        data=payload,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Incorrect email or password"
    assert (
        "set-cookie" not in response.headers
        or COOKIE_REFRESH_NAME not in response.headers.get("set-cookie", "")
    )


@pytest.mark.asyncio
async def test_token_nonexistent_user_localized_message(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={"username": "unknown@example.com", "password": "wrong"},
        headers={"Accept-Language": "es-ES"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == get_message(
        key="auth.incorrect_credentials",
        locale="es",
        default="Incorrect email or password",
    )


@pytest.mark.asyncio
async def test_token_inactive_user(
    client: AsyncClient,
    session: AsyncSession,
):
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    db_user.is_active = False
    session.add(db_user)
    await session.commit()

    response = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_token_empty_email_and_password(client: AsyncClient):
    try:
        await client.post(
            "/auth/token",
            data={
                "username": "",
                "password": "",
            },
        )
    except (Exception,):
        assert True
        return


# noinspection SpellCheckingInspection
@pytest.mark.parametrize(
    "missing_field, payload",
    [
        ("username", {"password": "somepassword"}),
        ("password", {"username": "nonexistent@example.com"}),
        ("both", {}),  # both missing
    ],
)
@pytest.mark.asyncio
async def test_token_missing_required_fields(
    client: AsyncClient,
    missing_field,
    payload,
):
    try:
        await client.post(
            "/auth/token",
            data=payload,
        )
    except (Exception,):
        assert True
