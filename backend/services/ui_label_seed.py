from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.ui_label import UiLabel
from models.ui_locale import UiLocale
from utils.murmur3 import murmurhash3_32

_PREFERRED_SEED_LOCALE_ORDER = (
    "en",
    "es",
    "fr",
    "de",
    "pt-BR",
    "zh-CN",
    "ja",
    "ko",
    "ar",
    "hi",
    "ru",
)
SEED_DIR = Path(__file__).resolve().parent.parent / "seed" / "ui_labels"


def list_seed_locales() -> list[str]:
    locales = sorted(file.stem for file in SEED_DIR.glob("*.json"))
    order_index = {locale: i for i, locale in enumerate(_PREFERRED_SEED_LOCALE_ORDER)}
    locales.sort(key=lambda locale: (order_index.get(locale, len(order_index)), locale))
    return locales


def _read_seed_locale(locale: str) -> dict[str, str]:
    file_path = SEED_DIR / f"{locale}.json"
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(k): str(v) for k, v in data.items()}


def _best_seed_locale(locale: str) -> str | None:
    seed_locales = list_seed_locales()
    if locale in seed_locales:
        return locale

    language = locale.split("-", 1)[0].lower()
    for seed_locale in seed_locales:
        if seed_locale.lower() == language:
            return seed_locale
        if seed_locale.lower().split("-", 1)[0] == language:
            return seed_locale

    return None


async def seed_ui_labels_for_locales(
    session: AsyncSession,
    locales: Iterable[str],
) -> None:
    english = _read_seed_locale("en")
    target_locales = sorted({*locales, "en"})

    for locale in target_locales:
        seed_locale = _best_seed_locale(locale)
        if not seed_locale:
            # Keep unsupported locales selectable without copying English labels.
            # Translations are created asynchronously by the existing add/translate flow.
            query = select(UiLabel).where(UiLabel.locale == locale, UiLabel.deleted_at == None)
            result = await session.execute(query)
            existing_labels = result.scalars().all()
            values = sorted([row.value for row in existing_labels])
            values_hash = murmurhash3_32("".join(values))

            locale_query = select(UiLocale).where(
                UiLocale.locale == locale,
                UiLocale.deleted_at == None,
            ).limit(1)
            locale_result = await session.execute(locale_query)
            locale_row = locale_result.scalars().first()

            if locale_row is None:
                session.add(UiLocale(locale=locale, values_hash=values_hash))
            else:
                locale_row.values_hash = values_hash
                session.add(locale_row)
            continue

        labels = dict(english)
        if seed_locale != "en":
            labels.update(_read_seed_locale(seed_locale))

        query = select(UiLabel).where(UiLabel.locale == locale, UiLabel.deleted_at == None)
        result = await session.execute(query)
        existing = {(row.key, row.locale): row for row in result.scalars().all()}

        for key, value in labels.items():
            row = existing.get((key, locale))
            if row is None:
                session.add(UiLabel(key=key, locale=locale, value=value))
                continue
            row.value = value
            session.add(row)

        values = sorted(labels.values())
        values_hash = murmurhash3_32("".join(values))

        locale_query = select(UiLocale).where(
            UiLocale.locale == locale,
            UiLocale.deleted_at == None,
        ).limit(1)
        locale_result = await session.execute(locale_query)
        locale_row = locale_result.scalars().first()

        if locale_row is None:
            session.add(UiLocale(locale=locale, values_hash=values_hash))
        else:
            locale_row.values_hash = values_hash
            session.add(locale_row)
