# /backend/tests/api/test_health.py

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.health import AppVersion
from main import app
from utils.db import get_session


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "Running"


@pytest.mark.asyncio
async def test_health_check_inactive_session(client, monkeypatch):
    # noinspection PyUnusedLocal
    async def mock_is_connected(session: AsyncSession):
        return False

    monkeypatch.setattr("api.health.is_connected", mock_is_connected)

    response = await client.get("/health")

    assert response.status_code == 500
    assert "Database session is not active" in response.text


@pytest.mark.asyncio
async def test_health_version(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["version"] == AppVersion.version


@pytest.mark.asyncio
async def test_health_exposes_app_name(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["app_name"] == "Test Site"


@pytest.mark.asyncio
async def test_health_returns_503_with_migration_hint_when_schema_is_missing(
    tmp_path: Path,
) -> None:
    sqlite_db = tmp_path / "unmigrated.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{sqlite_db}",
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def get_session_override():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as async_client:
            response = await async_client.get("/health")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    assert response.status_code == 503
    assert response.json()["status"] == "Unavailable"
    assert "alembic upgrade head" in response.json()["detail"]
