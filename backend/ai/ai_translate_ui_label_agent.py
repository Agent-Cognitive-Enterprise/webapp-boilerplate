# /backend/ai/ui_translate_agent.py

import logging

from ai.deepseek_ai_api_client import get_openai_response as get_deepseek_response
from ai.open_ai_api_client import get_openai_response
from services.system_settings import get_provider_api_key_from_db


logger = logging.getLogger(__name__)


def _is_provider_key_missing_error(exc: Exception) -> bool:
    return "api key is not configured" in str(exc).lower()


async def translate_english_to_locale(
    key: str,
    value_en: str,
    locale: str,
) -> str:
    """
    Translate the given English UI label value to the target locale using GPT.
    Placeholders wrapped with %...% must remain intact. If the target locale is 'en',
    return the input unchanged.
    """
    if locale.lower() == "en":
        return value_en

    openai_key = await get_provider_api_key_from_db("openai")
    deepseek_key = await get_provider_api_key_from_db("deepseek")
    if not openai_key and not deepseek_key:
        logger.info(
            "Skipping translation for locale %s: no AI provider API keys are configured.",
            locale,
        )
        return ""

    system = (
        "You are a precise UI translator. Preserve placeholders wrapped in % %, e.g. %user_name%. "
        "Do not alter their spelling or position. Translate only the surrounding text into the target language."
        "Note: UI key is provided for context where the text is used in UI."
    )
    prompt = (
        "Translate the following English UI label to the target language.\n\n"
        f"UI key (for context): {key}\n"
        f"Target language code: {locale}\n"
        f"Text: {value_en}\n\n"
        "Rules:\n"
        "- Keep %placeholders% unchanged.\n"
        "- Return only the translated phrase."
    )

    result: str | None = None

    if openai_key:
        try:
            result = await get_openai_response(
                prompt=prompt,
                model="gpt-4.1",
                max_tokens=120,
                temperature=0.2,
                system_prompt=system,
            )
        except Exception as openai_exc:
            logger.warning(
                "OpenAI translation failed for locale %s. Falling back to DeepSeek. Error: %s",
                locale,
                openai_exc,
            )
    else:
        logger.info(
            "OpenAI API key is not configured. Skipping OpenAI for locale %s.",
            locale,
        )

    if result is None and deepseek_key:
        try:
            result = await get_deepseek_response(
                prompt=prompt,
                model="deepseek-chat",
                max_tokens=120,
                temperature=0.2,
                system_prompt=system,
            )
        except Exception as deepseek_exc:
            if _is_provider_key_missing_error(deepseek_exc):
                logger.info(
                    "DeepSeek API key is not configured. Skipping DeepSeek for locale %s.",
                    locale,
                )
            else:
                logger.warning(
                    "DeepSeek translation failed for locale %s: %s",
                    locale,
                    deepseek_exc,
                )
            return ""
    elif result is None:
        logger.info(
            "DeepSeek API key is not configured. Translation unavailable for locale %s.",
            locale,
        )
        return ""

    return (result or "").strip()
