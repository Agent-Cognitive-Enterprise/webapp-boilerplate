# /backend/tests/api/test_health.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.health import AppVersion


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
