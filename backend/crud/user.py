# /backend/crud/user.py

import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, col

from models.user import User


async def create(
    session: AsyncSession,
    full_name: str,
    email: EmailStr,
    hashed_password: str,
    *,
    is_active: bool = True,
    is_superuser: bool = False,
    email_verified: bool = True,
    commit: bool = True,
) -> User:
    db_user = User(
        full_name=full_name,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_superuser=is_superuser,
        email_verified=email_verified,
    )
    session.add(db_user)
    if commit:
        await session.commit()

    return db_user


async def get_by_full_name(
    session: AsyncSession,
    full_name: str,
) -> User | None:
    result = await session.execute(
        select(User).where(
            and_(
                User.full_name == full_name,
                User.deleted_at == None,
            )
        )
    )

    return result.scalar_one_or_none()


async def get_by_email(
    session: AsyncSession,
    email: EmailStr,
) -> User | None:
    result = await session.execute(
        select(User).where(
            and_(
                User.email == email,
                User.deleted_at == None,
            )
        )
    )

    return result.scalar_one_or_none()


async def soft_delete(
    session: AsyncSession,
    user: User,
) -> User:
    user.deleted_at = datetime.datetime.now(datetime.UTC)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_full_names_by_ids(
    session: AsyncSession,
    user_ids: list[UUID],
    include_soft_deleted: bool = False,
) -> dict[str, str]:

    query = select(User.id, User.full_name).where(col(User.id).in_(user_ids))

    if not include_soft_deleted:
        query = query.where(User.deleted_at == None)

    result = await session.execute(query)
    users = result.all()

    output = {str(user.id): user.full_name for user in users}

    return output


async def get_all(
    session: AsyncSession,
) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.deleted_at == None)
        .order_by(User.created_at.desc())
    )
    return list(result.scalars().all())
