# /frontend/tests/conftest.py

"""Pytest configuration and fixtures for frontend Playwright tests."""
import asyncio
import os
import re
import signal
import socket
import subprocess
import sys
from queue import Queue
from pathlib import Path

import httpx
import pytest
import threading
import time
import uvicorn
from playwright.sync_api import sync_playwright
from backend.tests.test_env import TEST_AUTH_SECRET_KEY, TEST_INITIAL_SETUP_TOKEN

# NOTE: These environment variables must be set before importing any application code
os.environ.setdefault("DB_TYPE", "sqlite")
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
SQLITE_E2E_DB_PATH = str(BACKEND_DIR / "frontend_e2e.db")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


FAST_API_PORT = _find_free_port()
FRONTEND_PORT = _find_free_port()
FAST_API_BASE_URL = f"http://localhost:{FAST_API_PORT}"
FRONTEND_BASE_URL = f"http://localhost:{FRONTEND_PORT}"
os.environ.setdefault("SQLITE_DB_PATH", SQLITE_E2E_DB_PATH)
os.environ.setdefault("AUTH_SECRET_KEY", TEST_AUTH_SECRET_KEY)
os.environ.setdefault("INITIAL_SETUP_TOKEN", TEST_INITIAL_SETUP_TOKEN)
os.environ.setdefault("CORS_ALLOW_ORIGINS", FRONTEND_BASE_URL)
os.environ.setdefault("AUTH_FRONTEND_BASE_URL", FRONTEND_BASE_URL)
os.environ.setdefault("AUTH_BACKEND_BASE_URL", FAST_API_BASE_URL)

from main import app
from frontend.frontend_anchor import FrontendAnchor


FAST_API_HOST = "localhost"
VISUAL_ARTIFACTS_DIR = os.path.join(
    FrontendAnchor.get_location(),
    "tests",
    "artifacts",
)

# Make sure playwright with chromium is installed from /backend:
# python -m playwright install --with-deps chromium


# noinspection PyTypeChecker,HttpUrlsUsage
@pytest.fixture(scope="session", autouse=True)
def start_fastapi_server():
    """
    Launch FastAPI against a dedicated migrated SQLite database for Playwright.
    """
    if os.path.exists(SQLITE_E2E_DB_PATH):
        os.remove(SQLITE_E2E_DB_PATH)

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
        env=os.environ.copy(),
    )

    # Start Uvicorn in a thread
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=FAST_API_PORT,
        log_level="error",
        ws="websockets-sansio",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for it to come online
    for _ in range(20):
        try:
            resp = httpx.get(
                f"{FAST_API_BASE_URL}/health",
                timeout=1,
            )
            if resp.status_code == 200:
                break
        except (Exception,):
            time.sleep(0.2)
    else:
        raise RuntimeError("Backend did not start")

    yield

    server.should_exit = True
    thread.join(timeout=2)


# noinspection PyNoneFunctionAssignment,SpellCheckingInspection
def is_debugging() -> bool:
    """Check if a debugger is attached to enable headed browser mode."""
    trace = getattr(sys, "gettrace", lambda: None)()
    if trace is not None:
        return True
    # Extra fallbacks seen in PyCharm debug sessions
    return (
        os.getenv("PYCHARM_DEBUG") == "1"
        or os.getenv("PYDEVD_LOAD_VALUES_ASYNC") == "1"
    )


# noinspection PyTypeChecker
@pytest.fixture(scope="session", autouse=True)
def check_start_frontend_server():
    frontend_location = FrontendAnchor.get_location()

    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(FRONTEND_PORT)],
        cwd=frontend_location,
        env={
            **os.environ.copy(),
            "VITE_API_URL": FAST_API_BASE_URL,
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,  # allow killing process group
    )

    with httpx.Client() as client:
        for _ in range(30):
            try:
                res = client.get(
                    FRONTEND_BASE_URL,
                    timeout=1.0,
                )
                if res.status_code == 200:
                    break
            except httpx.RequestError:
                if process.poll() is not None:
                    raise RuntimeError("Frontend server exited before becoming ready.") from None
                time.sleep(1)
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            raise RuntimeError("Frontend server failed to start.")

    yield  # run tests

    os.killpg(
        os.getpgid(process.pid),
        signal.SIGTERM,
    )


@pytest.fixture(scope="function")
def browser_context():
    """Create a browser context for each test."""
    headless = not is_debugging()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=250)
        yield browser
        browser.close()


def _safe_file_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ui_locale(locale): run visual_page fixture context with the given browser locale",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def visual_page(browser_context, request):
    """
    Playwright page fixture with visual artifacts:
    - explicit step screenshots via the returned `snap()` helper
    - automatic failure screenshot
    - per-test UX checklist markdown scaffold
    """
    test_name = _safe_file_name(request.node.name)
    test_dir = os.path.join(VISUAL_ARTIFACTS_DIR, test_name)
    os.makedirs(test_dir, exist_ok=True)

    locale_marker = request.node.get_closest_marker("ui_locale")
    locale = None
    if locale_marker and locale_marker.args:
        locale = str(locale_marker.args[0])

    context_kwargs = {"viewport": {"width": 1440, "height": 900}}
    if locale:
        context_kwargs["locale"] = locale

    context = browser_context.new_context(**context_kwargs)
    page = context.new_page()
    page.set_default_timeout(10000)
    captured: list[str] = []

    def snap(label: str) -> str:
        idx = len(captured) + 1
        file_name = f"{idx:02d}_{_safe_file_name(label)}.png"
        path = os.path.join(test_dir, file_name)
        page.screenshot(path=path, full_page=True)
        captured.append(path)
        return path

    yield page, snap

    rep_call = getattr(request.node, "rep_call", None)
    if rep_call and rep_call.failed:
        snap("FAILED_STATE")

    checklist_path = os.path.join(test_dir, "ux_checklist.md")
    with open(checklist_path, "w", encoding="utf-8") as handle:
        handle.write("# UX Review Checklist\n\n")
        handle.write("- [ ] Labels/messages are understandable and not truncated\n")
        handle.write("- [ ] Layout is visually consistent and readable\n")
        handle.write("- [ ] User flow matches requested behavior\n")
        handle.write("- [ ] Sensitive fields are masked as expected\n")
        handle.write("- [ ] No confusing or stale helper text\n\n")
        handle.write("## Captured Screenshots\n")
        if captured:
            for path in captured:
                rel = os.path.relpath(path, FrontendAnchor.get_location())
                handle.write(f"- `{rel}`\n")
        else:
            handle.write("- (none)\n")

    context.close()


def run_async_safely(coro):
    """
    Run an async coroutine from sync code.
    - If no loop is running: use asyncio.run.
    - If a loop is running (e.g. Playwright sync): run in a worker thread.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread
        return asyncio.run(coro)

    # Running loop detected: execute in a separate thread

    q = Queue()

    def _runner():
        try:
            result = asyncio.run(coro)
            q.put((True, result))
        except BaseException as e:
            q.put((False, e))

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()

    ok, payload = q.get()
    if ok:
        return payload
    raise payload
