from collections.abc import Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import create_access_token
from main import PROTECTED_ADMIN_PATHS, PROTECTED_USER_PATHS
from tests.api.auth_session_test_helpers import (
    TRUSTED_ORIGIN,
    login_cookie_session,
)
from tests.api.protected_route_cases import (
    ADMIN_PROTECTED_ROUTE_PROBE_CASES,
    USER_AUTH_REQUIRED_GET_PATHS,
    USER_METHOD_DISCLOSURE_PATHS,
)
from tests.helper import create_test_user


ADMIN_PROBE_CASES = [
    pytest.param(
        case.method,
        case.path_factory,
        case.request_kwargs_factory,
        case.needs_csrf_origin,
        id=case.case_id,
    )
    for case in ADMIN_PROTECTED_ROUTE_PROBE_CASES
]


def test_shared_protected_route_cases_track_backend_guard_paths() -> None:
    admin_guard_paths = {case.guard_path for case in ADMIN_PROTECTED_ROUTE_PROBE_CASES}

    assert admin_guard_paths == {*PROTECTED_ADMIN_PATHS, "/users/{id}"}
    assert {*USER_AUTH_REQUIRED_GET_PATHS, *USER_METHOD_DISCLOSURE_PATHS} == PROTECTED_USER_PATHS


async def _login_cookie_session(
    client: AsyncClient,
    email: str,
    password: str,
) -> None:
    await login_cookie_session(client, email, password)


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
    unauthenticated_response = await client.get(USER_METHOD_DISCLOSURE_PATHS[0])

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"] == "Not authenticated"

    bearer_headers = await _authenticate_regular_user(
        client,
        session,
        "bearer",
        email="user-probe-bearer@example.com",
    )
    bearer_response = await client.get(
        USER_METHOD_DISCLOSURE_PATHS[0],
        headers=bearer_headers,
    )

    assert bearer_response.status_code == 405
    assert bearer_response.json()["detail"] == "Method Not Allowed"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", USER_AUTH_REQUIRED_GET_PATHS)
async def test_user_profile_routes_require_auth_before_response(
    client: AsyncClient,
    session: AsyncSession,
    path: str,
) -> None:
    unauthenticated_response = await client.get(path)

    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"] == "Not authenticated"

    bearer_headers = await _authenticate_regular_user(
        client,
        session,
        "bearer",
        email="users-me-probe@example.com",
    )
    authenticated_response = await client.get(path, headers=bearer_headers)

    assert authenticated_response.status_code == 200
    assert authenticated_response.json()["email"] == "users-me-probe@example.com"


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
