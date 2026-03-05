# /backend/tests/api/test_users.py
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from settings import AUTH_ALGORITHM, AUTH_SECRET_KEY
from tests.helper import create_test_user


@pytest.mark.asyncio
async def test_users_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/users/me/")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_users_me_authenticated(client: AsyncClient, session: AsyncSession):
    user = await create_test_user(
        session=session,
        full_name="Test User",
        email="testuser@example.com",
    )
    access_token = create_access_token(data={"sub": user.email})

    # Authenticated request to /users/me/
    user_me_resp = await client.get(
        "/users/me/", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert user_me_resp.status_code == 200

    data = user_me_resp.json()

    assert data["full_name"] == user.full_name
    assert data["email"] == user.email
    assert "id" in data


@pytest.mark.asyncio
async def test_users_me_rejects_malformed_sub_claim(client: AsyncClient):
    token = jwt.encode(
        {
            "sub": "not-an-email",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        AUTH_SECRET_KEY,
        algorithm=AUTH_ALGORITHM,
    )
    response = await client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

