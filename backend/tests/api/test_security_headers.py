import pytest
from httpx import AsyncClient


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
async def test_verify_email_html_feedback_uses_relaxed_inline_csp(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/auth/verify-email?token=invalid-token",
        headers={"Accept": "text/html"},
    )

    assert response.status_code == 400
    csp = response.headers.get("content-security-policy")
    assert csp is not None
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "frame-ancestors 'none'" in csp
