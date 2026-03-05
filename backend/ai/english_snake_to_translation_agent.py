# /backend/ai/english_snake_to_translation_agent.py

import re

from ai.open_ai_api_client import get_openai_response


def _extract_tail_snake(key: str) -> str:
    """
    Extract the last segment after the final dot. If there is no dot, return the key as-is.
    Example: "user_dashboard.header.welcome_to_x" => "welcome_to_x"
    """
    if not key:
        return key
    if "." in key:
        return key.split(".")[-1]
    return key


def _preserve_placeholders(text: str) -> tuple[str, dict[str, str]]:
    """
    Replace %place_holder% with sentinel tokens to prevent LLM from changing them.
    Returns (masked_text, mapping)
    """
    mapping: dict[str, str] = {}
    idx = 0

    def repl(m: re.Match) -> str:
        nonlocal idx
        token = f"__PH_{idx}__"
        mapping[token] = m.group(0)
        idx += 1
        return token

    masked = re.sub(r"%[^%]+%", repl, text)
    return masked, mapping


def _restore_placeholders(text: str, mapping: dict[str, str]) -> str:
    for token, placeholder in mapping.items():
        text = text.replace(token, placeholder)
    return text


async def snake_key_to_english_value(key: str) -> str:
    """
    Converts the tail of a dotted snake_case UI key into an English human-friendly sentence.
    Uses GPT-4.1-mini via get_openai_response. Placeholders wrapped with %...% must be preserved.

    Example:
    key = "user_dashboard.header.welcome_to_your_dashboard_%user_name%_at_%platform_name%"
    -> "Welcome to your dashboard %user_name% at %platform_name%"
    """
    tail = _extract_tail_snake(key)
    # Mask placeholders to prevent any mutation by the model
    masked_tail, mapping = _preserve_placeholders(tail)

    system_prompt = (
        "You convert English snake_case identifiers into a clean, user-facing English phrase. "
        "Do not translate to another language. Keep masked placeholders unchanged. "
        "Capitalize the sentence naturally."
    )

    user_prompt = (
        "Convert the following snake_case into a natural English UI label.\n\n"
        f"snake: {masked_tail}\n\n"
        "Rules:\n"
        "- Do not add punctuation at the end unless obvious.\n"
        "- Keep masked placeholders like __PH_0__ exactly as-is.\n"
        "- Return only the final phrase."
    )

    try:
        response = await get_openai_response(
            prompt=user_prompt,
            model="gpt-4.1-mini",
            max_tokens=80,
            temperature=0.0,
            system_prompt=system_prompt,
        )
        text = response.strip()
        # Basic fallback if model returns quotes or code fences
        text = re.sub(r"^[`\"]+|[`\"]+$", "", text)
    except (Exception,):
        # Deterministic fallback: simple snake -> words with preserved placeholders
        words = masked_tail.split("_")
        text = " ".join(w for w in words if w)
        if text:
            text = text[0].upper() + text[1:]

    final_text = _restore_placeholders(text, mapping)
    return final_text
