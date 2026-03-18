# /backend/crud/ui_locale.py

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from sqlmodel import and_, col, select
from datetime import datetime, timezone

from models.ui_locale import UiLocale


async def create(
    session: AsyncSession,
    locale: str,
    values_hash: str,
) -> UiLocale:
    ui_locale = UiLocale(
        locale=locale,
        values_hash=values_hash,
    )
    session.add(ui_locale)
    await session.commit()

    return ui_locale


async def get_list(
    session: AsyncSession,
) -> list[UiLocale]:
    query = select(UiLocale).where(
        col(UiLocale.deleted_at).is_(None),
    )
    result = await session.execute(query)

    return list(result.scalars().all())


async def get_by_locale(
    session: AsyncSession,
    locale: str,
) -> UiLocale | None:
    query = (
        select(UiLocale)
        .where(
            and_(
                UiLocale.locale == locale,
                col(UiLocale.deleted_at).is_(None),
            )
        )
        .limit(1)
    )
    result = await session.execute(query)

    return result.scalars().first()


async def update_values_hash(
    session: AsyncSession,
    locale: str,
    values_hash: str,
) -> UiLocale:
    db_ui_locale = await get_by_locale(
        session=session,
        locale=locale,
    )

    if db_ui_locale is None:
        return await create(
            session=session,
            locale=locale,
            values_hash=values_hash,
        )

    db_ui_locale.values_hash = values_hash
    session.add(db_ui_locale)
    await session.commit()

    return db_ui_locale


async def count(
    session: AsyncSession,
) -> int:
    query = select(func.count(col(UiLocale.id))).where(
        col(UiLocale.deleted_at).is_(None),
    )
    result = await session.execute(query)

    return int(result.scalar() or 0)


async def soft_delete(
    session: AsyncSession,
    locale: str,
) -> None:
    db_ui_locale = await get_by_locale(
        session=session,
        locale=locale,
    )

    if db_ui_locale is None:
        return

    db_ui_locale.deleted_at = datetime.now(timezone.utc)
    session.add(db_ui_locale)
    await session.commit()
