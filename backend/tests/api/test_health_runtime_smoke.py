import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from tests.test_env import TEST_AUTH_SECRET_KEY, TEST_INITIAL_SETUP_TOKEN


BACKEND_DIR = Path(__file__).resolve().parents[2]
SERVER_START_TIMEOUT_SECONDS = 15


def test_migrated_sqlite_server_returns_200(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "migrated.db"
    env = _build_server_env(sqlite_db)

    _run_alembic_upgrade(env)

    port = _find_free_port()
    process = _start_server(env, port)
    try:
        response = _wait_for_health_response(process, port, expected_status_code=200)
    finally:
        output = _stop_server(process)

    assert response.json()["status"] == "Running"
    assert "Traceback" not in output


def test_unmigrated_sqlite_server_returns_503_without_traceback(
    tmp_path: Path,
) -> None:
    sqlite_db = tmp_path / "unmigrated.db"
    env = _build_server_env(sqlite_db)

    port = _find_free_port()
    process = _start_server(env, port)
    try:
        response = _wait_for_health_response(process, port, expected_status_code=503)
    finally:
        output = _stop_server(process)

    assert response.json()["status"] == "Unavailable"
    assert "alembic upgrade head" in response.json()["detail"]
    assert "Exception in ASGI application" not in output
    assert "Traceback" not in output


def _build_server_env(sqlite_db: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "",
            "DB_TYPE": "sqlite",
            "SQLITE_DB_PATH": str(sqlite_db),
            "AUTH_SECRET_KEY": TEST_AUTH_SECRET_KEY,
            "INITIAL_SETUP_TOKEN": TEST_INITIAL_SETUP_TOKEN,
        }
    )
    return env


def _run_alembic_upgrade(env: dict[str, str]) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _start_server(env: dict[str, str], port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "info",
        ],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _wait_for_health_response(
    process: subprocess.Popen[str],
    port: int,
    *,
    expected_status_code: int,
) -> httpx.Response:
    deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
    url = f"http://127.0.0.1:{port}/health"
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            break

        try:
            response = httpx.get(url, timeout=1.0)
        except httpx.HTTPError as exc:
            last_error = exc
            time.sleep(0.1)
            continue

        if response.status_code == expected_status_code:
            return response

        last_error = AssertionError(
            f"Expected {expected_status_code} from /health, got {response.status_code}: {response.text}"
        )
        time.sleep(0.1)

    output = _stop_server(process)
    if last_error is not None:
        raise AssertionError(f"Server did not become ready. Output:\n{output}") from last_error
    raise AssertionError(f"Server exited before /health became ready. Output:\n{output}")


def _stop_server(process: subprocess.Popen[str]) -> str:
    if process.poll() is None:
        process.terminate()
        try:
            stdout, _ = process.communicate(timeout=5)
            return stdout
        except subprocess.TimeoutExpired:
            process.kill()

    stdout, _ = process.communicate(timeout=5)
    return stdout


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
