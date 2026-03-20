from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.ui_label_models import UILabelResponse
from api.ui_label_support import build_ui_label_map, compute_ui_label_values_hash
from crud.ui_label import create as create_label
from crud.ui_label import get_by_key_locale
from crud.ui_label import get_list_by_locale
from crud.ui_label_suggestions import create as create_suggestion
from crud.ui_locale import create as create_locale
from crud.ui_locale import get_by_locale
from crud.ui_locale import get_list as get_ui_locale_list
from i18n.messages import msg
from models.ui_label import UiLabel

GetCurrentUser = Callable[..., Awaitable[object | None]]
ScheduleTranslation = Callable[..., Awaitable[None]]
ScheduleSuggestionEvaluation = Callable[..., Awaitable[None]]


def locale_is_blank(locale: str | None) -> bool:
    return not locale or locale.strip() == ""


def locale_required_response(request: Request) -> UILabelResponse:
    return UILabelResponse(
        success=False,
        message=msg(
            request=request,
            key="ui_label.locale_required",
            default="locale is required",
        ),
    )


def unknown_action_response(request: Request) -> UILabelResponse:
    return UILabelResponse(
        success=False,
        message=msg(
            request=request,
            key="ui_label.unknown_action",
            default="Unknown action",
        ),
    )


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


async def _get_or_create_locale_metadata(
    session: AsyncSession,
    locale: str,
):
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
    db_ui_locale, db_locale_labels = await _get_or_create_locale_metadata(
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


async def handle_add_action(
    request: Request,
    session: AsyncSession,
    locale: str,
    key: str | None,
    schedule_translation: ScheduleTranslation,
) -> UILabelResponse:
    if not key:
        return UILabelResponse(
            success=False,
            message=msg(
                request=request,
                key="ui_label.key_required_for_add",
                default="key required for add",
            ),
        )

    existing_label = await get_by_key_locale(
        session=session,
        key=key,
        locale=locale,
    )
    if existing_label:
        return UILabelResponse(
            success=True,
            message=msg(
                request=request,
                key="ui_label.label_exists",
                default="label already exists",
            ),
        )

    await schedule_translation(
        key=key,
        target_locale=locale,
    )

    return UILabelResponse(
        success=True,
        message=msg(
            request=request,
            key="ui_label.translation_scheduled",
            default="scheduled for translation",
        ),
    )


async def handle_suggest_action(
    request: Request,
    session: AsyncSession,
    token: str,
    locale: str,
    key: str | None,
    value: str | None,
    get_current_user: GetCurrentUser,
    schedule_suggestion_evaluation: ScheduleSuggestionEvaluation,
) -> UILabelResponse:
    current_user = await get_current_user(
        token=token,
        session=session,
    )
    if not current_user or not hasattr(current_user, "id"):
        raise HTTPException(
            status_code=401,
            detail=msg(
                request=request,
                key="ui_label.unauthorized",
                default="Unauthorized",
            ),
        )

    if not key or not value:
        return UILabelResponse(
            success=False,
            message=msg(
                request=request,
                key="ui_label.key_value_required_for_suggest",
                default="key and value required for suggest",
            ),
        )

    db_ui_label_locale = await get_by_key_locale(
        session=session,
        key=key,
        locale=locale,
    )
    if not db_ui_label_locale:
        db_ui_label_locale = await create_label(
            session=session,
            key=key,
            locale=locale,
            value=value,
        )

    try:
        db_ui_label_suggestion = await create_suggestion(
            session=session,
            label_id=db_ui_label_locale.id,
            user_id=current_user.id,
            value=value,
        )
    except Exception:
        return UILabelResponse(
            success=False,
            message=msg(
                request=request,
                key="ui_label.suggestion_failed",
                default="failed to submit suggestion, try again later or contact support.",
            ),
        )

    if db_ui_label_locale.value != db_ui_label_suggestion.value:
        await schedule_suggestion_evaluation(ui_label=db_ui_label_locale)

    return UILabelResponse(
        success=True,
        message=msg(
            request=request,
            key="ui_label.suggestion_submitted",
            default="suggestion submitted",
        ),
    )
