from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.ui_label_models import UILabelResponse
from api.ui_label_support import build_ui_label_map, compute_ui_label_values_hash
from crud.ui_label import get_list_by_locale
from crud.ui_locale import create as create_locale
from crud.ui_locale import get_by_locale
from crud.ui_locale import get_list as get_ui_locale_list
from i18n.messages import msg
from models.ui_label import UiLabel


async def handle_list_action(
    request: Request,
    session: AsyncSession,
) -> UILabelResponse:
    db_ui_locale = await get_ui_locale_list(session=session)
    return UILabelResponse(
        success=True,
        data={"locales": [locale.locale for locale in db_ui_locale]},
        message=msg(
            request=request,
            key="ui_label.fetched_locales",
            default="fetched UI locales",
        ),
    )


async def get_or_create_locale_metadata(
    session: AsyncSession,
    locale: str,
) -> tuple[object, list[UiLabel] | None]:
    db_ui_locale = await get_by_locale(
        session=session,
        locale=locale,
    )
    db_locale_labels: list[UiLabel] | None = None

    if not db_ui_locale:
        db_locale_labels = await get_list_by_locale(
            session=session,
            locale=locale,
        )
        db_ui_locale = await create_locale(
            session=session,
            locale=locale,
            values_hash=compute_ui_label_values_hash(
                label.value for label in db_locale_labels
            ),
        )

    return db_ui_locale, db_locale_labels


async def handle_get_action(
    request: Request,
    session: AsyncSession,
    locale: str,
    values_hash: str | None,
) -> UILabelResponse:
    db_ui_locale, db_locale_labels = await get_or_create_locale_metadata(
        session=session,
        locale=locale,
    )

    if values_hash and db_ui_locale.values_hash == values_hash:
        return UILabelResponse(
            success=True,
            data={"values_hash": db_ui_locale.values_hash},
            message=msg(
                request=request,
                key="ui_label.no_changes",
                default="no changes",
            ),
        )

    if db_locale_labels is None:
        db_locale_labels = await get_list_by_locale(
            session=session,
            locale=locale,
        )

    return UILabelResponse(
        success=True,
        data={
            "locale": locale,
            "values_hash": db_ui_locale.values_hash,
            "labels": build_ui_label_map(db_locale_labels),
        },
        message=msg(
            request=request,
            key="ui_label.fetched",
            default="fetched",
        ),
    )
