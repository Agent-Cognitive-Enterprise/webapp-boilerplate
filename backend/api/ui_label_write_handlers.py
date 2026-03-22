from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.ui_label_models import UILabelResponse
from crud.ui_label import create as create_label
from crud.ui_label import get_by_key_locale
from crud.ui_label_suggestions import create as create_suggestion
from i18n.messages import msg

GetCurrentUser = Callable[..., Awaitable[object | None]]
ScheduleTranslation = Callable[..., Awaitable[None]]
ScheduleSuggestionEvaluation = Callable[..., Awaitable[None]]


@dataclass(frozen=True)
class SuggestActionInput:
    token: str | None
    locale: str
    key: str | None
    value: str | None


@dataclass(frozen=True)
class SuggestActionDependencies:
    get_current_user: GetCurrentUser
    schedule_suggestion_evaluation: ScheduleSuggestionEvaluation


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
    action_input: SuggestActionInput,
    dependencies: SuggestActionDependencies,
) -> UILabelResponse:
    current_user = await dependencies.get_current_user(
        request=request,
        token=action_input.token,
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

    if not action_input.key or not action_input.value:
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
        key=action_input.key,
        locale=action_input.locale,
    )
    if not db_ui_label_locale:
        db_ui_label_locale = await create_label(
            session=session,
            key=action_input.key,
            locale=action_input.locale,
            value=action_input.value,
        )

    try:
        db_ui_label_suggestion = await create_suggestion(
            session=session,
            label_id=db_ui_label_locale.id,
            user_id=current_user.id,
            value=action_input.value,
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
        await dependencies.schedule_suggestion_evaluation(ui_label=db_ui_label_locale)

    return UILabelResponse(
        success=True,
        message=msg(
            request=request,
            key="ui_label.suggestion_submitted",
            default="suggestion submitted",
        ),
    )
