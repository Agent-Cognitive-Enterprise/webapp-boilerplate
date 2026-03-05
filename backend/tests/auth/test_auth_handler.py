import pytest
# /backend/tests/auth/test_auth_handler.py

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import authenticate_user
from tests.utils.test_password import test_password, test_wrong_password
from utils.password import get_password_hash
from crud.user import create as create_user
from utils.helper import to_email_str

test_email: EmailStr = to_email_str("test.user@example.net")
wrong_email: EmailStr = to_email_str("wrong@email.net")


@pytest.mark.asyncio
async def test_authenticate_user(session: AsyncSession):

    hashed_password = get_password_hash(test_password)
    # Create a test user
    await create_user(
        session=session,
        full_name="Test User",
        email=test_email,
        hashed_password=hashed_password,
    )

    # Authenticate with correct credentials
    authenticated_user = await authenticate_user(
        session=session, email=test_email, password=test_password
    )

    assert authenticated_user is not False
    assert authenticated_user.email == test_email

    # Authenticate with an incorrect password
    assert (
        await authenticate_user(
            session=session, email=test_email, password=test_wrong_password
        )
        is False
    )

    # Authenticate with non-existent email
    assert (
        await authenticate_user(
            session=session, email=wrong_email, password=test_password
        )
        is False
    )

    # Inactive user must not authenticate
    inactive_user = await create_user(
        session=session,
        full_name="Inactive User",
        email=to_email_str("inactive@example.net"),
        hashed_password=hashed_password,
    )
    inactive_user.is_active = False
    session.add(inactive_user)
    await session.commit()

    assert (
        await authenticate_user(
            session=session,
            email=to_email_str("inactive@example.net"),
            password=test_password,
        )
        is False
    )
