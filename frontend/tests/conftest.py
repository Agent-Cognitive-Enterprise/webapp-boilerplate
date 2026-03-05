# /frontend/tests/conftest.py

"""
Pytest configuration and fixtures for E2E tests.

This module provides fixtures for:
- Multi-user browser contexts with storage state
- Playwright browser instances
- API clients for backend testing
- Database utilities for verification
"""
import asyncio
import os
import signal
import subprocess
import sys
import re
from queue import Queue
from uuid import UUID

import httpx
import logging
from playwright.sync_api import sync_playwright
import threading
import time
import pytest
import uvicorn

# NOTE: These environment variables must be set before importing any application code
os.environ.setdefault("DB_TYPE", "sqlite")
os.environ.setdefault(
    "AUTH_SECRET_KEY", "test-secret-key-for-e2e-tests-only-not-for-production-use"
)
os.environ.setdefault("INITIAL_SETUP_TOKEN", "test-initial-setup-token")

from main import app
from frontend.frontend_anchor import FrontendAnchor
from crud.user import get_by_email
from utils.db import get_session

try:
    from crud.message import get_session_history as get_session_history_messages
except ModuleNotFoundError:  # pragma: no cover - optional legacy module
    get_session_history_messages = None

try:
    from crud.opus import get_by_user_id as get_opuses_by_user_id
except ModuleNotFoundError:  # pragma: no cover - optional legacy module
    get_opuses_by_user_id = None

try:
    from crud.opus_contributor import is_contributor as is_contributor_crud
except ModuleNotFoundError:  # pragma: no cover - optional legacy module
    is_contributor_crud = None

try:
    from crud.chapter_draft import get_by_opus_id_and_title
except ModuleNotFoundError:  # pragma: no cover - optional legacy module
    get_by_opus_id_and_title = None


class FileFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Show only logs originating from this file
        return (
            os.path.basename(record.pathname) == "test_frontend_e2e.py"
            or os.path.basename(record.pathname) == "test_frontend_e2e_selenium.py"
        )


# Apply the filter globally
logger = logging.getLogger()
for handler in logger.handlers:
    handler.addFilter(FileFilter())


FAST_API_HOST = "localhost"
FAST_API_PORT = 8000
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
    Launch FastAPI using in-memory SQLite and share it with Playwright.
    """
    # Start Uvicorn in a thread
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=FAST_API_PORT,
        log_level="error",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for it to come online
    for _ in range(20):
        try:
            resp = httpx.get(
                f"http://{FAST_API_HOST}:{FAST_API_PORT}/health",
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


def check_frontend_server_running(client) -> bool:
    """Check if the frontend server is already running on port 5173."""
    try:
        res = client.get(
            "http://localhost:5173",
            timeout=1.0,
        )
        return res.status_code == 200
    except httpx.RequestError:
        return False


# noinspection PyTypeChecker
@pytest.fixture(scope="session", autouse=True)
def check_start_frontend_server():
    # Check whether the frontend server is already running on port 5173 -> if yes, skip starting it
    with httpx.Client() as client:
        if check_frontend_server_running(client):
            yield  # Server already running, yield
            return

        # Starts the Vite frontend via `npm run dev` and ensures it's live before tests.
        frontend_location = FrontendAnchor.get_location()

        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_location,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # allow a killing process group
        )

        # Wait for the frontend to become available
        for _ in range(30):
            if check_frontend_server_running(client):
                break
            time.sleep(1)
        else:
            process.terminate()
            raise RuntimeError("Frontend server failed to start.")

        yield  # run tests

        # Teardown
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


def get_db_user_records(user_email: str):
    # noinspection PyTypeChecker
    async def db_task():
        user = None
        async for session in get_session():
            user = await get_by_email(
                session=session,
                email=user_email,
            )

        return user

    return run_async_safely(db_task())


def get_db_opus_records(user_id: UUID):
    if get_opuses_by_user_id is None:
        pytest.skip("crud.opus is not available in this backend build")

    async def db_task():
        opuses: list = []
        async for session in get_session():
            opuses = await get_opuses_by_user_id(
                session=session,
                user_id=user_id,
            )

        return opuses

    return run_async_safely(db_task())


def check_db_is_opus_contributor(user_id: UUID, opus_id: UUID) -> bool:
    if is_contributor_crud is None:
        pytest.skip("crud.opus_contributor is not available in this backend build")

    async def db_task():
        is_contributor = False
        async for session in get_session():

            is_contributor = await is_contributor_crud(
                session=session,
                opus_id=opus_id,
                user_id=user_id,
            )

        return is_contributor

    return run_async_safely(db_task())


def get_db_path_messages(path: str):
    if get_session_history_messages is None:
        pytest.skip("crud.message is not available in this backend build")

    async def db_task():
        messages = []
        async for session in get_session():
            messages = await get_session_history_messages(
                session=session,
                path=path,
            )

        return messages

    return run_async_safely(db_task())


def get_db_opus_chapter_draft(opus_id: UUID, title: str):
    if get_by_opus_id_and_title is None:
        pytest.skip("crud.chapter_draft is not available in this backend build")

    async def db_task():
        db_chapter_draft = None
        async for session in get_session():
            db_chapter_draft = await get_by_opus_id_and_title(
                session=session,
                opus_id=opus_id,
                title=title,
            )

        return db_chapter_draft

    return run_async_safely(db_task())
