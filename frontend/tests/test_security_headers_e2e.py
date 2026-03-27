import httpx
import pytest

from frontend.tests.conftest import FAST_API_BASE_URL, FRONTEND_BASE_URL


EXPECTED_HSTS = "max-age=31536000; includeSubDomains"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/login",
        "/dashboard",
        "/admin/settings",
    ],
)
def test_frontend_routes_emit_clickjacking_and_transport_headers(path: str) -> None:
    response = httpx.get(
        f"{FRONTEND_BASE_URL}{path}",
        timeout=5.0,
    )

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["strict-transport-security"] == EXPECTED_HSTS

    csp = response.headers.get("content-security-policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "https://fonts.googleapis.com" in csp
    assert "https://fonts.gstatic.com" in csp
    assert FAST_API_BASE_URL in csp
