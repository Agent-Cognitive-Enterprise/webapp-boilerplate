# /backend/tests/api/test_users.py
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from settings import AUTH_ALGORITHM, AUTH_SECRET_KEY
from tests.helper import create_test_user


async def _create_admin_token(session: AsyncSession, email: str = "admin@example.com") -> str:
    admin = await create_test_user(session=session, email=email)
    admin.is_superuser = True
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return create_access_token(data={"sub": admin.email})


def _users_route_payload(method: str) -> dict | None:
    if method == "post":
        return {
            "full_name": "Managed User",
            "email": "managed@example.com",
            "password": "ManagedPass123!",
            "is_admin": False,
            "is_active": True,
        }
    if method == "put":
        return {"is_active": False}
    return None


def _users_request_kwargs(method: str) -> dict:
    payload = _users_route_payload(method)
    return {"json": payload} if payload is not None else {}


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/users"),
        ("post", "/users"),
        ("put", "/users/{user_id}"),
        ("delete", "/users/{user_id}"),
    ],
)
async def test_admin_user_routes_require_auth(
    client: AsyncClient,
    session: AsyncSession,
    method: str,
    path: str,
):
    managed_user = await create_test_user(session=session, email="managed-route@example.com")
    request_path = path.format(user_id=managed_user.id)
    response = await getattr(client, method)(
        request_path,
        **_users_request_kwargs(method),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/users"),
        ("post", "/users"),
        ("put", "/users/{user_id}"),
        ("delete", "/users/{user_id}"),
    ],
)
async def test_admin_user_routes_require_admin(
    client: AsyncClient,
    session: AsyncSession,
    method: str,
    path: str,
):
    user = await create_test_user(session=session, email="regular-route@example.com")
    managed_user = await create_test_user(session=session, email="managed-route-non-admin@example.com")
    token = create_access_token(data={"sub": user.email})
    request_path = path.format(user_id=managed_user.id)
    response = await getattr(client, method)(
        request_path,
        headers={"Authorization": f"Bearer {token}"},
        **_users_request_kwargs(method),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


@pytest.mark.asyncio
async def test_users_detail_get_requires_admin_before_method_disclosure(
    client: AsyncClient,
    session: AsyncSession,
):
    user_detail_path = f"/users/{uuid4()}"

    unauthenticated_response = await client.get(user_detail_path)
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"] == "Not authenticated"

    regular_user = await create_test_user(session=session, email="detail-regular@example.com")
    regular_token = create_access_token(data={"sub": regular_user.email})
    non_admin_response = await client.get(
        user_detail_path,
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert non_admin_response.status_code == 403
    assert non_admin_response.json()["detail"] == "Admin access required"

    admin_token = await _create_admin_token(session=session, email="detail-admin@example.com")
    admin_response = await client.get(
        user_detail_path,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_response.status_code == 405
    assert admin_response.json()["detail"] == "Method Not Allowed"
