# /backend/crud/ui_label_suggestions.py

import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import (
    select,
    and_,
    func,
)

from crud.helper import normalize_ui_label_value
from models.ui_label_suggestions import UiLabelSuggestion


async def create(
    session: AsyncSession,
    label_id: uuid.UUID,
    user_id: uuid.UUID,
    value: str,
) -> UiLabelSuggestion:
    suggestion = UiLabelSuggestion(
        label_id=label_id,
        user_id=user_id,
        value=normalize_ui_label_value(value),
    )
    session.add(suggestion)
    await session.commit()

    return suggestion


async def get_label_suggestions(
    session: AsyncSession,
    label_id: uuid.UUID,
) -> dict[str, int]:
    """
    For all non-soft-deleted suggestions get as dictionary with keys as suggested values and counts of the same
    suggestions.
    """
    stmt = (
        select(UiLabelSuggestion.value, func.count(UiLabelSuggestion.id))
        .where(
            and_(
                UiLabelSuggestion.label_id == label_id,
                UiLabelSuggestion.deleted_at == None,
            )
        )
        .group_by(UiLabelSuggestion.value)
    )

    results = await session.execute(stmt)

    return {value: count for value, count in results}


async def soft_delete(
    session: AsyncSession,
    suggestion: UiLabelSuggestion,
) -> UiLabelSuggestion:
    suggestion.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    session.add(suggestion)
    await session.commit()

    return suggestion
