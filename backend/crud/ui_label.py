# /backend/crud/ui_label.py

import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import (
    select,
    and_,
)

from crud.helper import normalize_ui_label_value
from models.ui_label import UiLabel


async def create(
    session: AsyncSession,
    key: str,
    locale: str,
    value: str,
) -> UiLabel:
    # Check whether the label already exists
    existing = await get_by_key_locale(
        session=session,
        key=key,
        locale=locale,
    )

    if existing:
        updated = await update(
            session=session,
            label=existing,
        )

        return updated

    label = UiLabel(
        key=key,
        locale=locale,
        value=normalize_ui_label_value(value),
    )
    session.add(label)
    await session.commit()

    return label


async def get_by_key_locale(
    session: AsyncSession,
    key: str,
    locale: str,
) -> Optional[UiLabel]:
    query = (
        select(UiLabel)
        .where(
            and_(
                UiLabel.key == key,
                UiLabel.locale == locale,
                UiLabel.deleted_at == None,
            )
        )
        .limit(1)
    )
    result = await session.execute(query)

    return result.scalars().first()


async def get_list_by_locale(
    session: AsyncSession,
    locale: str,
) -> List[UiLabel]:
    query = select(UiLabel).where(
        and_(
            UiLabel.locale == locale,
            UiLabel.deleted_at == None,
        )
    )
    result = await session.execute(query)

    return list(result.scalars().all())


# noinspection DuplicatedCode
async def update(
    session: AsyncSession,
    label: UiLabel,
) -> UiLabel:

    label.value = normalize_ui_label_value(label.value)

    persisted = await session.merge(label)
    await session.commit()

    return persisted


async def soft_delete(
    session: AsyncSession,
    label: UiLabel,
) -> UiLabel:
    label.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    session.add(label)
    await session.commit()
    await session.refresh(label)

    return label
