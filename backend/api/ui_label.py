# /backend/api/ui_label.py

import asyncio
import logging
from typing import (
    Any,
    List,
    Optional,
    Dict,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ui_label import (
    get_by_key_locale,
    get_list_by_locale,
    create as create_label,
    update as update_label,
)
from crud.ui_label_suggestions import (
    create as create_suggestion,
    get_label_suggestions,
)
from crud.ui_locale import (
    get_by_locale,
    create as create_locale,
    update_values_hash,
    get_list as get_ui_locale_list,
)
from models.ui_label import UiLabel
from utils.db import (
    get_session,
    AsyncSessionLocal,
)
from auth.auth_handler import (
    get_current_user,
    oauth2_scheme,
)
from ai.english_snake_to_translation_agent import snake_key_to_english_value
from ai.ai_translate_ui_label_agent import translate_english_to_locale
from ai.ai_suggestion_evaluation_agent import evaluate_label_suggestions
from utils.murmur3 import murmurhash3_32
from i18n.messages import msg

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------
# Request / Response models
# ------------------------------
class UILabelRequest(BaseModel):
    action: str  # "get" | "add" | "suggest" | "list" (locale)
    locale: Optional[str] = None  # e.g. "en", "fr", "es"
    # For "get" FE should compute the hash of values to avoid refetching.
    # If hash matches, BE should just return the matching hash response.
    # If hash doesn't match or is not provided, BE should return all labels for the locale.
    values_hash: Optional[str] = None  # User MurmurHash3
    key: Optional[str] = None  # For "add" or "suggest"
    value: Optional[str] = None  # For "suggest"


class UILabelResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None


async def schedule_translation(
    key: str,
    target_locale: str,
):
    async def _worker():
        try:
            async with AsyncSessionLocal() as session:
                # If already exists, skip
                if await get_by_key_locale(
                    session=session,
                    key=key,
                    locale=target_locale,
                ):
                    return

                # Get an English label
                db_ui_label_en: UiLabel | None = await get_by_key_locale(
                    session=session,
                    key=key,
                    locale="en",
                )
                # Generate English value from a snake-case key and create
                if not db_ui_label_en:
                    value_en = await snake_key_to_english_value(key=key)
                    if not value_en:
                        logger.warning(f"Cannot generate English label for key {key}")
                        return

                    # Create the English label
                    try:
                        db_ui_label_en = await create_label(
                            session=session,
                            key=key,
                            locale="en",
                            value=value_en,
                        )
                    except (Exception,):
                        logger.warning(
                            f"Failed to create ui-label for {key} in en, it may already exist"
                        )
                        return

                value_locale = await translate_english_to_locale(
                    key=key,
                    value_en=db_ui_label_en.value,
                    locale=target_locale,
                )
                logger.info(f"Translated label {key} to {target_locale}: {value_locale}")

                if not value_locale:
                    logger.warning(f"Cannot translate label {key} to {target_locale}")
                    return

                # Try creating the locale-specific label
                try:
                    await create_label(
                        session=session,
                        key=key,
                        locale=target_locale,
                        value=value_locale,
                    )
                except (Exception,):
                    logger.warning(
                        f"Failed to create ui-label for {key} in {target_locale}, it may already exist"
                    )
                    return

                # Compute a new hash for the locale
                db_locale_labels: List[UiLabel] = await get_list_by_locale(
                    session=session,
                    locale=target_locale,
                )
                locale_values = [label.value for label in db_locale_labels]
                locale_values.sort()
                new_values_hash = murmurhash3_32("".join(locale_values))

                # Update or create the UiLocale entry
                try:
                    await update_values_hash(
                        session=session,
                        locale=target_locale,
                        values_hash=new_values_hash,
                    )
                except (Exception,):
                    logger.exception(
                        f"Failed to update values_hash for locale {target_locale}"
                    )

        except (Exception,):
            logger.exception("Background translation failed")

    asyncio.create_task(_worker())


async def schedule_suggestion_evaluation(ui_label: UiLabel):
    async def _worker():
        session = None
        try:
            # Yield briefly to let the request transaction finish when sharing the same session in tests
            await asyncio.sleep(0.01)
            # AsyncSessionLocal may be a session factory or a monkeypatched shared session.
            # Always close in finally to prevent leaked sqlite worker threads.
            session = AsyncSessionLocal()
            # Get suggested values with counts
            db_ui_label_suggestions = await get_label_suggestions(
                session=session,
                label_id=ui_label.id,
            )

            best_value = await evaluate_label_suggestions(
                ui_label=ui_label,
                suggestions=db_ui_label_suggestions,
            )

            # Nothing to change
            if not best_value or best_value == ui_label.value:
                return

            # Update label with the best suggestion
            ui_label.value = best_value
            try:
                await update_label(
                    session=session,
                    label=ui_label,
                )
            except (Exception,):
                logger.exception("Failed to update ui_label with best suggestion")
                return

            # After updating a label in a locale, recompute the locale hash
            try:
                db_locale_labels: List[UiLabel] = await get_list_by_locale(
                    session=session,
                    locale=ui_label.locale,
                )
                locale_values = [label.value for label in db_locale_labels]
                locale_values.sort()
                new_values_hash = murmurhash3_32("".join(locale_values))

                await update_values_hash(
                    session=session,
                    locale=ui_label.locale,
                    values_hash=new_values_hash,
                )
            except (Exception,):
                logger.exception(
                    f"Failed to update values_hash for locale {ui_label.locale} after suggestion evaluation"
                )

        except (Exception,):
            logger.exception("Background suggestion evaluation failed")
        finally:
            if session is not None:
                try:
                    await session.close()
                except (Exception,):
                    logger.debug("Failed to close background suggestion session")

    asyncio.create_task(_worker())


# ------------------------------
# /ui-label POST endpoint
# ------------------------------
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
        db_ui_locale = await get_ui_locale_list(
            session=session,
        )

        return UILabelResponse(
            success=True,
            data={
                "locales": [locale.locale for locale in db_ui_locale],
            },
            message=msg(
                request=request,
                key="ui_label.fetched_locales",
                default="fetched UI locales",
            ),
        )

    if request_body.locale.strip() == "":
        return UILabelResponse(
            success=False,
            message=msg(
                request=request,
                key="ui_label.locale_required",
                default="locale is required",
            ),
        )

    # --------------------------
    # GET labels, no authentication required
    # --------------------------
    if action == "get":
        db_ui_locale = await get_by_locale(
            session=session,
            locale=request_body.locale,
        )

        db_locale_labels: List[UiLabel] | None = None

        if not db_ui_locale:
            # Create a locale with computed hash
            db_locale_labels: List[UiLabel] = await get_list_by_locale(
                session=session,
                locale=request_body.locale,
            )
            # Extract values for hash computation
            locale_values = [label.value for label in db_locale_labels]
            # Sort them alphabetically to ensure a consistent hash
            locale_values.sort()
            # Compute a new hash
            new_values_hash = murmurhash3_32("".join(locale_values))

            db_ui_locale = await create_locale(
                session=session,
                locale=request_body.locale,
                values_hash=new_values_hash,
            )

        if (
            request_body.values_hash
            and db_ui_locale.values_hash == request_body.values_hash
        ):
            return UILabelResponse(
                success=True,
                data={"values_hash": db_ui_locale.values_hash},
                message=msg(
                    request=request,
                    key="ui_label.no_changes",
                    default="no changes",
                ),
            )

        # Fetch labels for requested locale
        if not db_locale_labels:
            db_locale_labels: List[UiLabel] = await get_list_by_locale(
                session=session,
                locale=request_body.locale,
            )

        # Convert to dict for response
        result_labels: Dict[str, str] = {
            label.key: label.value for label in db_locale_labels
        }

        return UILabelResponse(
            success=True,
            data={
                "locale": request_body.locale,
                "values_hash": db_ui_locale.values_hash,
                "labels": result_labels,
            },
            message=msg(
                request=request,
                key="ui_label.fetched",
                default="fetched",
            ),
        )

    # --------------------------
    # ADD translation, authentication not required
    # --------------------------
    if action == "add":
        if not request_body.key:
            return UILabelResponse(
                success=False,
                message=msg(
                    request=request,
                    key="ui_label.key_required_for_add",
                    default="key required for add",
                ),
            )

        # Check if the label already exists
        existing_label = await get_by_key_locale(
            session=session,
            key=request_body.key,
            locale=request_body.locale,
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

        # Schedule background translation
        await schedule_translation(
            key=request_body.key,
            target_locale=request_body.locale,
        )

        return UILabelResponse(
            success=True,
            message=msg(
                request=request,
                key="ui_label.translation_scheduled",
                default="scheduled for translation",
            ),
        )

    # --------------------------
    # SUGGEST translation, authentication required
    # --------------------------
    if action == "suggest":
        current_user = await get_current_user(
            token=token,
            session=session,
        )
        # Require authentication for suggestions
        if not current_user or not hasattr(current_user, "id"):
            raise HTTPException(
                status_code=401,
                detail=msg(
                    request=request,
                    key="ui_label.unauthorized",
                    default="Unauthorized",
                ),
            )
        # Require key and value
        if not request_body.key or not request_body.value:
            return UILabelResponse(
                success=False,
                message=msg(
                    request=request,
                    key="ui_label.key_value_required_for_suggest",
                    default="key and value required for suggest",
                ),
            )
        # Find the label_id (create if missing)
        db_ui_label_locale: UiLabel = await get_by_key_locale(
            session=session,
            key=request_body.key,
            locale=request_body.locale,
        )
        if not db_ui_label_locale:
            db_ui_label_locale = await create_label(
                session=session,
                key=request_body.key,
                locale=request_body.locale,
                value=request_body.value,
            )

        try:
            db_ui_label_suggestion = await create_suggestion(
                session=session,
                label_id=db_ui_label_locale.id,
                user_id=current_user.id,
                value=request_body.value,
            )
        except (Exception,):
            return UILabelResponse(
                success=False,
                message=msg(
                    request=request,
                    key="ui_label.suggestion_failed",
                    default="failed to submit suggestion, try again later or contact support.",
                ),
            )

        # Schedule background suggestion evaluation if it is a new suggestion
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

    return UILabelResponse(
        success=False,
        message=msg(
            request=request,
            key="ui_label.unknown_action",
            default="Unknown action",
        ),
    )
