import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/setup",
        "/setup/email/check",
        "/auth/register",
    ],
)
async def test_malformed_json_returns_bad_request(
    client: AsyncClient,
    path: str,
) -> None:
    response = await client.post(
        path,
        content=b"{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail[0]["type"] == "json_invalid"
    assert detail[0]["loc"] == ["body", 1]


@pytest.mark.asyncio
async def test_schema_validation_errors_remain_unprocessable_entity(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "full_name": "Validation Test",
            "email": "not-an-email",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "email"]
