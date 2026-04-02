from collections.abc import Callable
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from tests.helper import create_test_user


TRUSTED_ORIGIN = "http://localhost:5173"


def _empty_request_kwargs() -> dict[str, object]:
    return {}


def _admin_settings_post_kwargs() -> dict[str, object]:
    return {"json": {}}


def _user_detail_path() -> str:
    return f"/users/{uuid4()}"


def _static_path(path: str) -> Callable[[], str]:
    return lambda: path


ADMIN_PROBE_CASES = [
    pytest.param(
        "get",
        _static_path("/admin/settings"),
        _empty_request_kwargs,
        False,
        id="admin-settings-get",
    ),
    pytest.param(
        "post",
        _static_path("/admin/settings"),
        _admin_settings_post_kwargs,
        True,
        id="admin-settings-post",
    ),
    pytest.param(
        "get",
        _static_path("/admin/settings/email/check"),
        _empty_request_kwargs,
        False,
        id="admin-settings-email-check-get",
    ),
    pytest.param(
        "get",
        _static_path("/users"),
        _empty_request_kwargs,
        False,
        id="users-list-get",
    ),
    pytest.param(
        "get",
        _user_detail_path,
        _empty_request_kwargs,
        False,
        id="users-detail-get",
    ),
]


async def _login_cookie_session(
    client: AsyncClient,
    email: str,
    password: str,
) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200


async def _authenticate_regular_user(
    client: AsyncClient,
    session: AsyncSession,
    auth_mode: str,
    *,
    email: str,
) -> dict[str, str]:
    password = "ProtectedRouteProbePass123!"
    user = await create_test_user(
        session=session,
        email=email,
        password=password,
    )

    if auth_mode == "bearer":
        return {"Authorization": f"Bearer {create_access_token(data={'sub': user.email})}"}

    await _login_cookie_session(client, user.email, password)
    return {}


async def _probe(
    client: AsyncClient,
    method: str,
    path_factory: Callable[[], str],
    request_kwargs_factory: Callable[[], dict[str, object]],
    *,
    headers: dict[str, str] | None = None,
):
    return await client.request(
        method.upper(),
        path_factory(),
        headers=headers,
        **request_kwargs_factory(),
    )


@pytest.mark.asyncio
async def test_user_probe_requires_auth_before_method_disclosure(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    unauthenticated_response = await client.get("/user-settings")

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"] == "Not authenticated"

    bearer_headers = await _authenticate_regular_user(
        client,
        session,
        "bearer",
        email="user-probe-bearer@example.com",
    )
    bearer_response = await client.get("/user-settings", headers=bearer_headers)

    assert bearer_response.status_code == 405
    assert bearer_response.json()["detail"] == "Method Not Allowed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path_factory", "request_kwargs_factory", "needs_csrf_origin"),
    ADMIN_PROBE_CASES,
)
async def test_admin_probe_matrix_unauthenticated_requests_are_challenged(
    client: AsyncClient,
    method: str,
    path_factory: Callable[[], str],
    request_kwargs_factory: Callable[[], dict[str, object]],
    needs_csrf_origin: bool,
) -> None:
    del needs_csrf_origin

    response = await _probe(
        client,
        method,
        path_factory,
        request_kwargs_factory,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_mode", ["bearer", "cookie"])
@pytest.mark.parametrize(
    ("method", "path_factory", "request_kwargs_factory", "needs_csrf_origin"),
    ADMIN_PROBE_CASES,
)
async def test_admin_probe_matrix_non_admin_requests_are_forbidden(
    client: AsyncClient,
    session: AsyncSession,
    auth_mode: str,
    method: str,
    path_factory: Callable[[], str],
    request_kwargs_factory: Callable[[], dict[str, object]],
    needs_csrf_origin: bool,
) -> None:
    headers = await _authenticate_regular_user(
        client,
        session,
        auth_mode,
        email=f"admin-probe-{auth_mode}@example.com",
    )
    if auth_mode == "cookie" and needs_csrf_origin:
        headers["Origin"] = TRUSTED_ORIGIN

    response = await _probe(
        client,
        method,
        path_factory,
        request_kwargs_factory,
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"
