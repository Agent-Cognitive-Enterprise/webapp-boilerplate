import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.user import User


@pytest.mark.asyncio
async def test_register_without_email_config_is_immediately_verified(
    client: AsyncClient,
    session: AsyncSession,
):
    response = await client.post(
        "/auth/register",
        json={
            "full_name": "No Mail User",
            "email": "nomail@example.com",
            "password": "NoMailPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    user_result = await session.execute(
        select(User).where(User.email == "nomail@example.com")
    )
    user = user_result.scalars().first()
    assert user is not None
    assert user.email_verified is True
