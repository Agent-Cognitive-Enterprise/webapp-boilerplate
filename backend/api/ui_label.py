# /backend/api/ui_label.py

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai.ai_suggestion_evaluation_agent import evaluate_label_suggestions
from ai.ai_translate_ui_label_agent import translate_english_to_locale
from ai.english_snake_to_translation_agent import snake_key_to_english_value
from api.ui_label_background import schedule_suggestion_evaluation_task
from api.ui_label_background import schedule_translation_task
from api.ui_label_handlers import handle_add_action
from api.ui_label_handlers import handle_get_action
from api.ui_label_handlers import handle_list_action
from api.ui_label_handlers import handle_suggest_action
from api.ui_label_handlers import locale_is_blank
from api.ui_label_handlers import locale_required_response
from api.ui_label_handlers import unknown_action_response
from api.ui_label_handlers import SuggestActionDependencies
from api.ui_label_handlers import SuggestActionInput
from api.ui_label_models import UILabelRequest
from api.ui_label_models import UILabelResponse
from auth.auth_handler import get_current_user, oauth2_scheme
from crud.ui_label import create as create_label
from crud.ui_label import get_by_key_locale
from crud.ui_label import get_list_by_locale
from crud.ui_label import update as update_label
from crud.ui_label_suggestions import get_label_suggestions
from crud.ui_locale import update_values_hash
from models.ui_label import UiLabel
from utils.db import AsyncSessionLocal, get_session

logger = logging.getLogger(__name__)
router = APIRouter()


async def schedule_translation(
    key: str,
    target_locale: str,
) -> None:
    await schedule_translation_task(
        key=key,
        target_locale=target_locale,
        session_factory=AsyncSessionLocal,
        get_label_by_key_locale=get_by_key_locale,
        create_label=create_label,
        get_labels_by_locale=get_list_by_locale,
        update_values_hash=update_values_hash,
        snake_key_to_english_value=snake_key_to_english_value,
        translate_english_to_locale=translate_english_to_locale,
    )


async def schedule_suggestion_evaluation(ui_label: UiLabel) -> None:
    await schedule_suggestion_evaluation_task(
        ui_label=ui_label,
        session_factory=AsyncSessionLocal,
        get_labels_by_locale=get_list_by_locale,
        get_label_suggestions=get_label_suggestions,
        evaluate_label_suggestions=evaluate_label_suggestions,
        update_label=update_label,
        update_values_hash=update_values_hash,
    )


@router.post(
    "/ui-label",
    response_model=UILabelResponse,
)
async def ui_label_post(
    request: Request,
    request_body: UILabelRequest,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    action = request_body.action.lower()

    if action == "list":
        return await handle_list_action(
            request=request,
            session=session,
        )

    if locale_is_blank(request_body.locale):
        return locale_required_response(request)

    locale = request_body.locale or ""

    if action == "get":
        return await handle_get_action(
            request=request,
            session=session,
            locale=locale,
            values_hash=request_body.values_hash,
        )

    if action == "add":
        return await handle_add_action(
            request=request,
            session=session,
            locale=locale,
            key=request_body.key,
            schedule_translation=schedule_translation,
        )

    if action == "suggest":
        return await handle_suggest_action(
            request=request,
            session=session,
            action_input=SuggestActionInput(
                token=token,
                locale=locale,
                key=request_body.key,
                value=request_body.value,
            ),
            dependencies=SuggestActionDependencies(
                get_current_user=get_current_user,
                schedule_suggestion_evaluation=schedule_suggestion_evaluation,
            ),
        )

    return unknown_action_response(request)
