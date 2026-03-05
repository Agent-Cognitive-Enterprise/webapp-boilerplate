from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import Request

SEED_DIR = Path(__file__).resolve().parents[1] / "seed" / "api_messages"
DEFAULT_LOCALE = "en"


def _normalize_locale(value: str | None) -> str:
    if not value:
        return DEFAULT_LOCALE
    locale = value.strip().replace("_", "-")
    if not locale:
        return DEFAULT_LOCALE
    return locale


def _parse_accept_language(header_value: str | None) -> str:
    if not header_value:
        return DEFAULT_LOCALE
    first = header_value.split(",", 1)[0]
    candidate = first.split(";", 1)[0].strip()
    return _normalize_locale(candidate)


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    for file in sorted(SEED_DIR.glob("*.json")):
        with file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        catalog[file.stem] = {str(k): str(v) for k, v in data.items()}
    return catalog


def resolve_locale(request: Request | None) -> str:
    if request is None:
        return DEFAULT_LOCALE

    accept = request.headers.get("accept-language")
    locale = _parse_accept_language(accept)

    catalog = _load_catalog()
    if locale in catalog:
        return locale

    language = locale.split("-", 1)[0].lower()
    for candidate in catalog:
        if candidate.lower() == language:
            return candidate
        if candidate.lower().split("-", 1)[0] == language:
            return candidate

    return DEFAULT_LOCALE


def get_message(key: str, locale: str, default: str | None = None) -> str:
    catalog = _load_catalog()
    normalized_locale = _normalize_locale(locale)

    if normalized_locale in catalog and key in catalog[normalized_locale]:
        return catalog[normalized_locale][key]

    if key in catalog.get(DEFAULT_LOCALE, {}):
        return catalog[DEFAULT_LOCALE][key]

    return default if default is not None else key


def msg(
    *,
    request: Request | None,
    key: str,
    default: str,
) -> str:
    return get_message(key=key, locale=resolve_locale(request), default=default)
