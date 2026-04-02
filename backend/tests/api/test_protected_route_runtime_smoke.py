from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

import httpx

from security.csrf import CSRF_ERROR_DETAIL
from tests.api.runtime_smoke_helpers import (
    build_server_env,
    find_free_port,
    run_alembic_upgrade,
    start_server,
    stop_server,
    wait_for_health_response,
)
from tests.test_env import TEST_INITIAL_SETUP_TOKEN


REGULAR_USER_EMAIL = "runtime-user@example.com"
REGULAR_USER_PASSWORD = "RuntimeUserPass123!"
ADMIN_EMAIL = "runtime-admin@example.com"
ADMIN_PASSWORD = "RuntimeAdminPass123!"
TRUSTED_ORIGIN = "http://localhost:5173"
UNTRUSTED_ORIGIN = "http://evil.example"
ADMIN_PROBE_PATHS: tuple[Callable[[], str], ...] = (
    lambda: "/admin/settings",
    lambda: "/users",
    lambda: f"/users/{uuid4()}",
)


def test_live_server_protected_routes_require_auth_and_admin(
    tmp_path: Path,
) -> None:
    sqlite_db = tmp_path / "protected-routes.db"
    env = build_server_env(sqlite_db)

    run_alembic_upgrade(env)

    port = find_free_port()
    process = start_server(env, port)
    output = ""
    try:
        wait_for_health_response(process, port, expected_status_code=200)
        base_url = f"http://127.0.0.1:{port}"

        with (
            httpx.Client(base_url=base_url, timeout=2.0) as guest_client,
            httpx.Client(base_url=base_url, timeout=2.0) as user_client,
            httpx.Client(base_url=base_url, timeout=2.0) as admin_client,
        ):
            _initialize_application(guest_client)
            _register_regular_user(guest_client)
            _login(user_client, REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD)
            admin_token = _login(admin_client, ADMIN_EMAIL, ADMIN_PASSWORD)

            for path_factory in ADMIN_PROBE_PATHS:
                guest_response = guest_client.get(path_factory())
                assert guest_response.status_code == 401
                assert guest_response.json()["detail"] == "Not authenticated"

                user_response = user_client.get(path_factory())
                assert user_response.status_code == 403
                assert user_response.json()["detail"] == "Admin access required"

            trusted_origin_response = user_client.post(
                "/admin/settings",
                json={},
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert trusted_origin_response.status_code == 403
            assert trusted_origin_response.json()["detail"] == "Admin access required"

            untrusted_origin_response = user_client.post(
                "/admin/settings",
                json={},
                headers={"Origin": UNTRUSTED_ORIGIN},
            )
            assert untrusted_origin_response.status_code == 403
            assert untrusted_origin_response.json()["detail"] == CSRF_ERROR_DETAIL

            user_settings_trusted_origin_response = user_client.post(
                "/user-settings",
                json={"route": "/profile", "settings": {"locale": "fr"}},
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert user_settings_trusted_origin_response.status_code == 200
            assert user_settings_trusted_origin_response.json()["route"] == "/profile"
            assert user_settings_trusted_origin_response.json()["settings"] == {"locale": "fr"}

            user_settings_untrusted_origin_response = user_client.post(
                "/user-settings",
                json={"route": "/profile", "settings": {"locale": "de"}},
                headers={"Origin": UNTRUSTED_ORIGIN},
            )
            assert user_settings_untrusted_origin_response.status_code == 403
            assert user_settings_untrusted_origin_response.json()["detail"] == CSRF_ERROR_DETAIL

            admin_response = admin_client.get(
                f"/users/{uuid4()}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert admin_response.status_code == 405
            assert admin_response.json()["detail"] == "Method Not Allowed"
    finally:
        output = stop_server(process)

    assert "Exception in ASGI application" not in output
    assert "Traceback" not in output


def _initialize_application(client: httpx.Client) -> None:
    response = client.post(
        "/setup",
        json={
            "setup_token": TEST_INITIAL_SETUP_TOKEN,
            "site_name": "Runtime Smoke",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": ADMIN_EMAIL,
            "admin_password": ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text


def _register_regular_user(client: httpx.Client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Runtime User",
            "email": REGULAR_USER_EMAIL,
            "password": REGULAR_USER_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text


def _login(client: httpx.Client, email: str, password: str) -> str:
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
