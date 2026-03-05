from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from main import app
from utils.db import get_session


@pytest.fixture(autouse=True)
def clear_setup_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    # E2E tests should not depend on developer-local .env setup defaults.
    for env_key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_USE_TLS",
        "AUTH_FRONTEND_BASE_URL",
        "AUTH_BACKEND_BASE_URL",
    ):
        monkeypatch.delenv(env_key, raising=False)


@pytest_asyncio.fixture
async def e2e_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def e2e_client(
    e2e_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with e2e_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def e2e_db_session(
    e2e_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with e2e_session_factory() as session:
        yield session
