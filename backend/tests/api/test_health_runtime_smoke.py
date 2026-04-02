from pathlib import Path

from tests.api.runtime_smoke_helpers import (
    build_server_env,
    find_free_port,
    run_alembic_upgrade,
    start_server,
    stop_server,
    wait_for_health_response,
)


def test_migrated_sqlite_server_returns_200(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "migrated.db"
    env = build_server_env(sqlite_db)

    run_alembic_upgrade(env)

    port = find_free_port()
    process = start_server(env, port)
    try:
        response = wait_for_health_response(process, port, expected_status_code=200)
    finally:
        output = stop_server(process)

    assert response.json()["status"] == "Running"
    assert "Traceback" not in output


def test_unmigrated_sqlite_server_returns_503_without_traceback(
    tmp_path: Path,
) -> None:
    sqlite_db = tmp_path / "unmigrated.db"
    env = build_server_env(sqlite_db)

    port = find_free_port()
    process = start_server(env, port)
    try:
        response = wait_for_health_response(process, port, expected_status_code=503)
    finally:
        output = stop_server(process)

    assert response.json()["status"] == "Unavailable"
    assert "alembic upgrade head" in response.json()["detail"]
    assert "Exception in ASGI application" not in output
    assert "Traceback" not in output
