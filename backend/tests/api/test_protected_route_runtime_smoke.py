from pathlib import Path
import sqlite3

import httpx

from auth.refresh_utils import hash_token
from settings import COOKIE_REFRESH_NAME, COOKIE_SESSION_BINDING_NAME
from security.csrf import CSRF_ERROR_DETAIL
from tests.api.auth_session_test_helpers import (
    TRUSTED_ORIGIN,
    UNTRUSTED_ORIGIN,
    assert_auth_cookie_delete_headers,
)
from tests.api.protected_route_cases import (
    ADMIN_GET_PROBE_PATH_FACTORIES,
    ADMIN_USER_DETAIL_PATH_FACTORY,
    USER_AUTH_REQUIRED_GET_PATHS,
)
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
            httpx.Client(base_url=base_url, timeout=2.0) as missing_refresh_client,
            httpx.Client(base_url=base_url, timeout=2.0) as invalid_refresh_client,
            httpx.Client(base_url=base_url, timeout=2.0) as rotation_client,
            httpx.Client(base_url=base_url, timeout=2.0) as binding_client,
            httpx.Client(base_url=base_url, timeout=2.0) as legacy_client,
            httpx.Client(base_url=base_url, timeout=2.0) as admin_client,
        ):
            _initialize_application(guest_client)
            _register_regular_user(guest_client)
            _login(user_client, REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD)
            _login(rotation_client, REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD)
            _login(binding_client, REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD)
            _login(legacy_client, REGULAR_USER_EMAIL, REGULAR_USER_PASSWORD)
            admin_token = _login(admin_client, ADMIN_EMAIL, ADMIN_PASSWORD)

            for path_factory in ADMIN_GET_PROBE_PATH_FACTORIES:
                guest_response = guest_client.get(path_factory())
                assert guest_response.status_code == 401
                assert guest_response.json()["detail"] == "Not authenticated"

                user_response = user_client.get(path_factory())
                assert user_response.status_code == 403
                assert user_response.json()["detail"] == "Admin access required"

            for path in USER_AUTH_REQUIRED_GET_PATHS:
                guest_response = guest_client.get(path)
                assert guest_response.status_code == 401
                assert guest_response.json()["detail"] == "Not authenticated"

                user_response = user_client.get(path)
                assert user_response.status_code == 200
                assert user_response.json()["email"] == REGULAR_USER_EMAIL

            _assert_refresh_missing_and_invalid_token_failures(
                missing_refresh_client=missing_refresh_client,
                invalid_refresh_client=invalid_refresh_client,
            )

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

            refresh_untrusted_origin_response = user_client.post(
                "/auth/refresh",
                headers={"Origin": UNTRUSTED_ORIGIN},
            )
            assert refresh_untrusted_origin_response.status_code == 403
            assert refresh_untrusted_origin_response.json()["detail"] == CSRF_ERROR_DETAIL

            refresh_trusted_origin_response = user_client.post(
                "/auth/refresh",
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert refresh_trusted_origin_response.status_code == 200
            assert refresh_trusted_origin_response.json()["token_type"] == "bearer"
            assert "access_token" in refresh_trusted_origin_response.json()

            post_refresh_user_settings_response = user_client.post(
                "/user-settings",
                json={"route": "/profile", "settings": {"locale": "it"}},
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert post_refresh_user_settings_response.status_code == 200
            assert post_refresh_user_settings_response.json()["settings"] == {"locale": "it"}

            _assert_refresh_rotation_reuse_detection(rotation_client)
            _assert_refresh_requires_matching_session_binding_cookie(binding_client)
            _assert_legacy_refresh_token_migration(legacy_client, sqlite_db)

            logout_untrusted_origin_response = user_client.post(
                "/auth/logout",
                headers={"Origin": UNTRUSTED_ORIGIN},
            )
            assert logout_untrusted_origin_response.status_code == 403
            assert logout_untrusted_origin_response.json()["detail"] == CSRF_ERROR_DETAIL

            logout_trusted_origin_response = user_client.post(
                "/auth/logout",
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert logout_trusted_origin_response.status_code == 204

            post_logout_user_settings_response = user_client.post(
                "/user-settings",
                json={"route": "/profile", "settings": {"locale": "en"}},
                headers={"Origin": TRUSTED_ORIGIN},
            )
            assert post_logout_user_settings_response.status_code == 401
            assert post_logout_user_settings_response.json()["detail"] == "Not authenticated"

            admin_response = admin_client.get(
                ADMIN_USER_DETAIL_PATH_FACTORY(),
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


def _assert_refresh_rotation_reuse_detection(client: httpx.Client) -> None:
    old_refresh_token = client.cookies.get(COOKIE_REFRESH_NAME)
    session_binding_token = client.cookies.get(COOKIE_SESSION_BINDING_NAME)

    assert old_refresh_token is not None
    assert session_binding_token is not None

    refresh_response = client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert refresh_response.status_code == 200

    new_refresh_token = client.cookies.get(COOKIE_REFRESH_NAME)
    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token

    client.cookies.set(COOKIE_REFRESH_NAME, old_refresh_token)
    client.cookies.set(COOKIE_SESSION_BINDING_NAME, session_binding_token)
    replay_response = client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert replay_response.status_code == 401
    assert replay_response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(replay_response)

    client.cookies.set(COOKIE_REFRESH_NAME, new_refresh_token)
    client.cookies.set(COOKIE_SESSION_BINDING_NAME, session_binding_token)
    descendant_response = client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert descendant_response.status_code == 401
    assert descendant_response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(descendant_response)


def _assert_refresh_requires_matching_session_binding_cookie(client: httpx.Client) -> None:
    refresh_token = client.cookies.get(COOKIE_REFRESH_NAME)

    assert refresh_token is not None

    client.cookies.set(COOKIE_SESSION_BINDING_NAME, "tampered-session-binding")
    refresh_response = client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(refresh_response)


def _assert_legacy_refresh_token_migration(
    client: httpx.Client,
    sqlite_db: Path,
) -> None:
    old_refresh_token = client.cookies.get(COOKIE_REFRESH_NAME)
    old_session_binding_token = client.cookies.get(COOKIE_SESSION_BINDING_NAME)

    assert old_refresh_token is not None
    assert old_session_binding_token is not None

    _set_client_binding_hash(sqlite_db, old_refresh_token, None)

    refresh_response = client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["token_type"] == "bearer"

    new_refresh_token = client.cookies.get(COOKIE_REFRESH_NAME)
    new_session_binding_token = client.cookies.get(COOKIE_SESSION_BINDING_NAME)
    assert new_refresh_token is not None
    assert new_session_binding_token is not None
    assert new_refresh_token != old_refresh_token
    assert new_session_binding_token != old_session_binding_token
    assert _get_client_binding_hash(sqlite_db, new_refresh_token) is not None

    post_migration_user_settings_response = client.post(
        "/user-settings",
        json={"route": "/profile", "settings": {"locale": "nl"}},
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert post_migration_user_settings_response.status_code == 200
    assert post_migration_user_settings_response.json()["settings"] == {"locale": "nl"}


def _assert_refresh_missing_and_invalid_token_failures(
    *,
    missing_refresh_client: httpx.Client,
    invalid_refresh_client: httpx.Client,
) -> None:
    missing_refresh_response = missing_refresh_client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert missing_refresh_response.status_code == 401
    assert missing_refresh_response.json()["detail"] == "Missing refresh token"
    assert_auth_cookie_delete_headers(missing_refresh_response)

    invalid_refresh_client.cookies.set(COOKIE_REFRESH_NAME, "notavalidtokenatall")
    invalid_refresh_client.cookies.set(
        COOKIE_SESSION_BINDING_NAME,
        "bogus-session-binding",
    )

    invalid_refresh_response = invalid_refresh_client.post(
        "/auth/refresh",
        headers={"Origin": TRUSTED_ORIGIN},
    )
    assert invalid_refresh_response.status_code == 401
    assert invalid_refresh_response.json()["detail"] == "Invalid refresh token"
    assert_auth_cookie_delete_headers(invalid_refresh_response)


def _set_client_binding_hash(
    sqlite_db: Path,
    refresh_token: str,
    client_binding_hash: str | None,
) -> None:
    with sqlite3.connect(sqlite_db) as connection:
        cursor = connection.execute(
            """
            UPDATE refresh_tokens
            SET client_binding_hash = ?
            WHERE token_hash = ? AND deleted_at IS NULL
            """,
            (client_binding_hash, hash_token(refresh_token)),
        )
        connection.commit()

    assert cursor.rowcount == 1


def _get_client_binding_hash(sqlite_db: Path, refresh_token: str) -> str | None:
    with sqlite3.connect(sqlite_db) as connection:
        row = connection.execute(
            """
            SELECT client_binding_hash
            FROM refresh_tokens
            WHERE token_hash = ? AND deleted_at IS NULL
            """,
            (hash_token(refresh_token),),
        ).fetchone()

    assert row is not None
    return row[0]
