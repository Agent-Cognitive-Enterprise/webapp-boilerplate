# /backend/tests/helper.py
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from crud.user import create as user_create
from models.user import User
from utils.password import get_password_hash
from auth.auth_handler import create_access_token

fake = Faker()


async def create_test_user(
    session: AsyncSession,
    full_name: str = None,
    email: str = None,
    password: str = "testpassword123",
    hashed_password: str = None,
) -> User:
    """Create a test user with optional custom fields."""
    if not full_name:
        full_name = fake.name()
    if not email:
        email = fake.email()

    # Use provided hashed_password or hash the password
    if hashed_password is None:
        hashed_password = get_password_hash(password)

    user = await user_create(
        session=session,
        full_name=full_name,
        email=email,
        hashed_password=hashed_password,
    )

    return user


async def create_test_token_and_user(session: AsyncSession, client=None):
    """Create a test user and generate an access token.

    Args:
        session: Database session
        client: Optional HTTP client (not used, for backwards compatibility)

    Returns:
        Tuple of (access_token, user)
    """
    user = await create_test_user(session)
    token = create_access_token(data={"sub": user.email})
    return token, user
