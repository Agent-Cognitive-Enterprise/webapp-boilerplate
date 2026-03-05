# /backend/tests/conftest.py

import os
from datetime import datetime, timezone

# Set environment variables for testing
os.environ.setdefault("DB_TYPE", "sqlite")
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("AUTH_RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("INITIAL_SETUP_TOKEN", "test-initial-setup-token")


import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from httpx import AsyncClient, ASGITransport
import logging
from fastapi.testclient import TestClient


from main import app
from models.system_settings import SystemSettings
from utils.db import get_session


logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True, scope="session")
def set_log_level():
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("fastapi").setLevel(logging.CRITICAL)
    logging.getLogger("root").setLevel(logging.CRITICAL)
    logging.getLogger("app").setLevel(logging.CRITICAL)


@pytest_asyncio.fixture(name="session")
async def session_fixture():
    # Create an in-memory SQLite async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Create the tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create a session maker bound to the engine
    async_session_local = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    # Provide a session to the test
    async with async_session_local() as session:
        session.add(
            SystemSettings(
                singleton_key="default",
                site_name="Test Site",
                default_locale="en",
                supported_locales=["en"],
                is_initialized=True,
                initialized_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
        yield session

    # Clean up the engine
    await engine.dispose()


# noinspection PyUnresolvedReferences
@pytest_asyncio.fixture(name="client")
async def client_fixture(session: AsyncSession):
    async def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


# noinspection PyUnresolvedReferences
@pytest.fixture(name="ws_client")
def ws_client_fixture(session: AsyncSession):
    """Sync WebSocket client using FastAPI's TestClient."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
