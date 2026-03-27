import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import HSTS_HEADER_VALUE, app
from utils.db import get_session


@pytest.mark.asyncio
async def test_health_response_sets_default_csp(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    csp = response.headers.get("content-security-policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-inline'" not in csp


@pytest.mark.asyncio
async def test_verify_email_html_feedback_uses_default_csp(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/auth/verify-email?token=invalid-token",
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    csp = response.headers.get("content-security-policy")
    assert csp is not None
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-inline'" not in csp


@pytest.mark.asyncio
async def test_unauthorized_admin_route_still_sets_clickjacking_headers(
    client: AsyncClient,
) -> None:
    response = await client.get("/admin/settings")

    assert response.status_code == 401
    assert response.headers["x-frame-options"] == "DENY"
    csp = response.headers.get("content-security-policy")
    assert csp is not None
    assert "frame-ancestors 'none'" in csp


@pytest.mark.asyncio
async def test_https_responses_set_hsts(session: AsyncSession) -> None:
    async def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="https://test",
        ) as client:
            response = await client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["strict-transport-security"] == HSTS_HEADER_VALUE


@pytest.mark.asyncio
async def test_http_responses_do_not_set_hsts(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert "strict-transport-security" not in response.headers
