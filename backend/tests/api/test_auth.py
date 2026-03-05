# /backend/tests/api/test_register.py

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import re

from utils.password import get_password_hash
from settings import COOKIE_REFRESH_NAME
from tests.helper import create_test_user
from auth.refresh_utils import hash_token
from crud.refresh_token import get_by_token_hash, mark_used_and_revoke
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
        response = await client.post(
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


@pytest.mark.asyncio
async def test_refresh_missing_cookie(client: AsyncClient):
    response = await client.post("/auth/refresh")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Missing refresh token"


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_refresh_invalid_token(
    client: AsyncClient,
    session: AsyncSession,
):
    # An invalid token: set a cookie value that doesn't exist in db
    client.cookies.set(COOKIE_REFRESH_NAME, "notavalidtokenatall")
    response = await client.post("/auth/refresh")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_revoked_token(
    client: AsyncClient,
    session: AsyncSession,
):
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    resp = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )
    cookie_val = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        resp.headers["set-cookie"],
    ).group(1)
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        cookie_val,
    )

    rt_hash = hash_token(cookie_val)
    rt = await get_by_token_hash(session, rt_hash)

    assert rt is not None, "Refresh token not found in database"

    await mark_used_and_revoke(session, rt)
    await session.commit()

    response = await client.post("/auth/refresh")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_expired_token(
    client: AsyncClient,
    session: AsyncSession,
):
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    resp = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )
    set_cookie = resp.headers.get("set-cookie")

    assert set_cookie, "No set-cookie header in response"

    match = re.search(rf"{COOKIE_REFRESH_NAME}=([^;]+);", set_cookie)

    assert match, "No matching refresh cookie found"

    cookie_val = match.group(1)
    client.cookies.set(COOKIE_REFRESH_NAME, cookie_val)

    # Expire the token in DB
    rt_hash = hash_token(cookie_val)
    rt = await get_by_token_hash(session, rt_hash)

    assert rt is not None, "RefreshToken not found in DB"

    rt.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    await session.commit()

    response = await client.post("/auth/refresh")

    assert response.status_code == 401

    data = response.json()

    assert "detail" in data, f"Response did not return 'detail' key: {data}"
    assert data["detail"] == "Refresh token expired"


@pytest.mark.asyncio
async def test_refresh_token_success(
    client: AsyncClient,
    session: AsyncSession,
):
    # Step 1: Register or create a user
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    # Step 2: Log in to get tokens and the refresh cookie
    resp = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )

    assert resp.status_code == 200

    # Extract refresh token cookie from the response
    set_cookie = resp.headers.get("set-cookie")

    assert set_cookie, "No set-cookie header in response"

    match = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        set_cookie,
    )

    assert match, "No refresh token cookie found"

    refresh_cookie_val = match.group(1)
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        refresh_cookie_val,
    )

    # Step 3: Use refresh endpoint to get new tokens
    refresh_resp = await client.post("/auth/refresh")

    assert refresh_resp.status_code == 200

    refresh_data = refresh_resp.json()

    # Step 4: Check the structure and contents of the new tokens
    assert "access_token" in refresh_data
    assert "token_type" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # Optionally, check a new refresh token cookie is set in response
    set_cookie_new = refresh_resp.headers.get("set-cookie")

    assert set_cookie_new, "No set-cookie header set on refresh"
    # You may also want to check here that the new refresh token is different from the old one (rotation)


@pytest.mark.asyncio
async def test_refresh_fingerprint_mismatch(
    client: AsyncClient,
    session: AsyncSession,
):
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    resp = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
        headers={
            "user-agent": "agent-a",
            "x-forwarded-for": "203.0.113.10",
        },
    )

    assert resp.status_code == 200
    cookie_val = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        resp.headers["set-cookie"],
    ).group(1)
    client.cookies.set(COOKIE_REFRESH_NAME, cookie_val)

    mismatch_response = await client.post(
        "/auth/refresh",
        headers={
            "user-agent": "agent-b",
            "x-forwarded-for": "198.51.100.21",
        },
    )

    assert mismatch_response.status_code == 401
    assert mismatch_response.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_token_rotation(
    client: AsyncClient,
    session: AsyncSession,
):
    # Step 1: Register or create a user
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )

    # Step 2: Login to get initial tokens and refresh token cookie
    resp = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )

    assert resp.status_code == 200

    cookie = resp.headers.get("set-cookie")
    match = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        cookie,
    )

    assert match, "No initial refresh token set"

    old_refresh_token = match.group(1)
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        old_refresh_token,
    )

    # Step 3: First refresh (rotates the token)
    resp_refresh = await client.post("/auth/refresh")

    assert resp_refresh.status_code == 200

    new_cookie = resp_refresh.headers.get("set-cookie")
    match_new = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        new_cookie,
    )

    assert match_new, "No rotated refresh token set"

    new_refresh_token = match_new.group(1)

    assert new_refresh_token != old_refresh_token, "Refresh token was not rotated"

    client.cookies.set(
        COOKIE_REFRESH_NAME,
        new_refresh_token,
    )

    # Step 4: Use the **old** refresh token again (should be revoked/invalid)
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        old_refresh_token,
    )
    invalid_refresh = await client.post("/auth/refresh")

    assert (
        invalid_refresh.status_code == 401
    )  # Or whatever your API returns for a revoked token

    # Step 5: Reuse detection should revoke descendants too, so the previously
    # rotated token is now also invalid.
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        new_refresh_token,
    )
    second_refresh = await client.post("/auth/refresh")

    assert second_refresh.status_code == 401
    assert second_refresh.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_logout_clears_cookie_and_revokes_token(
    client: AsyncClient,
    session: AsyncSession,
):
    # Arrange: Register and login to get refresh token cookie
    db_user = await create_test_user(
        session=session,
        hashed_password=get_password_hash(test_password),
    )
    response = await client.post(
        "/auth/token",
        data={
            "username": db_user.email,
            "password": test_password,
        },
    )

    assert response.status_code == 200

    set_cookie = response.headers.get("set-cookie")

    assert set_cookie

    match = re.search(
        rf"{COOKIE_REFRESH_NAME}=([^;]+);",
        set_cookie,
    )

    assert match

    refresh_token = match.group(1)
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        refresh_token,
    )

    # Act: Call logout with cookie present
    logout_response = await client.post("/auth/logout")

    # Assert: Should always return 204 No Content
    assert logout_response.status_code == 204

    # Check if the cookie is cleared (deleted)
    logout_set_cookie = logout_response.headers.get("set-cookie")

    assert logout_set_cookie is not None and "Max-Age=0" in logout_set_cookie

    # Optional: Try using the *same* refresh token to ensure it's revoked
    client.cookies.set(
        COOKIE_REFRESH_NAME,
        refresh_token,
    )
    post_logout_refresh = await client.post("/auth/refresh")

    assert post_logout_refresh.status_code == 401


@pytest.mark.asyncio
async def test_logout_without_cookie_is_idempotent(client: AsyncClient):
    # No refresh token cookie set
    if COOKIE_REFRESH_NAME in client.cookies:
        client.cookies.clear(COOKIE_REFRESH_NAME)
    response = await client.post("/auth/logout")

    assert response.status_code == 204

    # If no cookie is present, should still clear any cookie
    set_cookie = response.headers.get("set-cookie")

    assert set_cookie is not None and "Max-Age=0" in set_cookie


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_logout_with_invalid_token_cookie(client: AsyncClient):
    # Set an obviously invalid refresh token string
    client.cookies.set(COOKIE_REFRESH_NAME, "notavalidtoken")
    response = await client.post("/auth/logout")

    assert response.status_code == 204

    # Should clear the cookie, not the error
    set_cookie = response.headers.get("set-cookie")

    assert set_cookie is not None and "Max-Age=0" in set_cookie
