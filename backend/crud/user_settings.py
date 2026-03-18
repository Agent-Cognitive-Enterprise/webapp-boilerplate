# /backend/crud/user_settings.py

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, col, func, select

from models.user_settings import UserSettings
from schemas.user_settings import UserSettingsIn


async def upsert_user_settings(
    session: AsyncSession, user_id: UUID, data: UserSettingsIn
) -> UserSettings:
    result = await session.execute(
        select(UserSettings).where(
            and_(
                UserSettings.user_id == user_id,
                UserSettings.route == data.route,
            )
        )
    )
    user_settings = result.scalars().first()

    if user_settings:
        # Update existing
        user_settings.settings = data.settings or {}
        user_settings.updated_at = datetime.now(timezone.utc)
        user_settings.deleted_at = None
    else:
        # Insert new
        user_settings = UserSettings(
            user_id=user_id,
            route=data.route,
            settings=data.settings,
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        session.add(user_settings)

    await session.commit()
    await session.refresh(user_settings)

    return user_settings


async def get_user_settings(
    session: AsyncSession, user_id: UUID, route: str
) -> UserSettings | None:
    result = await session.execute(
        select(UserSettings).where(
            and_(
                UserSettings.user_id == user_id,
                UserSettings.route == route,
                col(UserSettings.deleted_at).is_(None),
            )
        )
    )

    return result.scalar_one_or_none()


async def soft_delete_user_settings(
    session: AsyncSession, user_id: UUID, route: str
) -> UserSettings | None:
    result = await session.execute(
        select(UserSettings).where(
            and_(
                UserSettings.user_id == user_id,
                UserSettings.route == route,
                col(UserSettings.deleted_at).is_(None),
            )
        )
    )
    user_settings = result.scalars().first()

    if user_settings:
        user_settings.deleted_at = datetime.now(timezone.utc)
        session.add(user_settings)
        await session.commit()
        await session.refresh(user_settings)

    return user_settings


async def count_user_settings(session: AsyncSession, user_id: UUID, route: str) -> int:
    result = await session.execute(
        select(func.count(col(UserSettings.id))).where(
            and_(
                UserSettings.user_id == user_id,
                UserSettings.route == route,
                col(UserSettings.deleted_at).is_(None),
            )
        )
    )

    return int(result.scalar() or 0)
