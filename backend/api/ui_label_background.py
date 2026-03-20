import asyncio
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from api.ui_label_support import compute_ui_label_values_hash
from models.ui_label import UiLabel

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]
GetLabelByKeyLocale = Callable[..., Awaitable[UiLabel | None]]
GetLabelsByLocale = Callable[..., Awaitable[list[UiLabel]]]
CreateLabel = Callable[..., Awaitable[UiLabel]]
UpdateLabel = Callable[..., Awaitable[UiLabel]]
UpdateValuesHash = Callable[..., Awaitable[object]]
SnakeKeyToEnglishValue = Callable[..., Awaitable[str | None]]
TranslateEnglishToLocale = Callable[..., Awaitable[str | None]]
GetLabelSuggestions = Callable[..., Awaitable[dict[str, int]]]
EvaluateLabelSuggestions = Callable[..., Awaitable[str | None]]


async def schedule_translation_task(
    key: str,
    target_locale: str,
    session_factory: SessionFactory,
    get_label_by_key_locale: GetLabelByKeyLocale,
    create_label: CreateLabel,
    get_labels_by_locale: GetLabelsByLocale,
    update_values_hash: UpdateValuesHash,
    snake_key_to_english_value: SnakeKeyToEnglishValue,
    translate_english_to_locale: TranslateEnglishToLocale,
) -> None:
    async def _worker() -> None:
        try:
            async with session_factory() as session:
                if await get_label_by_key_locale(
                    session=session,
                    key=key,
                    locale=target_locale,
                ):
                    return

                db_ui_label_en = await get_label_by_key_locale(
                    session=session,
                    key=key,
                    locale="en",
                )
                if not db_ui_label_en:
                    value_en = await snake_key_to_english_value(key=key)
                    if not value_en:
                        logger.warning("Cannot generate English label for key %s", key)
                        return

                    try:
                        db_ui_label_en = await create_label(
                            session=session,
                            key=key,
                            locale="en",
                            value=value_en,
                        )
                    except Exception:
                        logger.warning(
                            "Failed to create ui-label for %s in en, it may already exist",
                            key,
                        )
                        return

                value_locale = await translate_english_to_locale(
                    key=key,
                    value_en=db_ui_label_en.value,
                    locale=target_locale,
                )
                logger.info(
                    "Translated label %s to %s: %s",
                    key,
                    target_locale,
                    value_locale,
                )

                if not value_locale:
                    logger.warning(
                        "Cannot translate label %s to %s",
                        key,
                        target_locale,
                    )
                    return

                try:
                    await create_label(
                        session=session,
                        key=key,
                        locale=target_locale,
                        value=value_locale,
                    )
                except Exception:
                    logger.warning(
                        "Failed to create ui-label for %s in %s, it may already exist",
                        key,
                        target_locale,
                    )
                    return

                db_locale_labels = await get_labels_by_locale(
                    session=session,
                    locale=target_locale,
                )
                new_values_hash = compute_ui_label_values_hash(
                    label.value for label in db_locale_labels
                )

                try:
                    await update_values_hash(
                        session=session,
                        locale=target_locale,
                        values_hash=new_values_hash,
                    )
                except Exception:
                    logger.exception(
                        "Failed to update values_hash for locale %s",
                        target_locale,
                    )
        except Exception:
            logger.exception("Background translation failed")

    asyncio.create_task(_worker())


async def schedule_suggestion_evaluation_task(
    ui_label: UiLabel,
    session_factory: SessionFactory,
    get_labels_by_locale: GetLabelsByLocale,
    get_label_suggestions: GetLabelSuggestions,
    evaluate_label_suggestions: EvaluateLabelSuggestions,
    update_label: UpdateLabel,
    update_values_hash: UpdateValuesHash,
) -> None:
    async def _worker() -> None:
        session = None
        try:
            await asyncio.sleep(0.01)
            session = session_factory()

            db_ui_label_suggestions = await get_label_suggestions(
                session=session,
                label_id=ui_label.id,
            )
            best_value = await evaluate_label_suggestions(
                ui_label=ui_label,
                suggestions=db_ui_label_suggestions,
            )

            if not best_value or best_value == ui_label.value:
                return

            ui_label.value = best_value
            try:
                await update_label(
                    session=session,
                    label=ui_label,
                )
            except Exception:
                logger.exception("Failed to update ui_label with best suggestion")
                return

            try:
                db_locale_labels = await get_labels_by_locale(
                    session=session,
                    locale=ui_label.locale,
                )
                new_values_hash = compute_ui_label_values_hash(
                    label.value for label in db_locale_labels
                )

                await update_values_hash(
                    session=session,
                    locale=ui_label.locale,
                    values_hash=new_values_hash,
                )
            except Exception:
                logger.exception(
                    "Failed to update values_hash for locale %s after suggestion evaluation",
                    ui_label.locale,
                )
        except Exception:
            logger.exception("Background suggestion evaluation failed")
        finally:
            if session is not None:
                try:
                    await session.close()
                except Exception:
                    logger.debug("Failed to close background suggestion session")

    asyncio.create_task(_worker())
