import json
from pathlib import Path

import pytest

SEED_DIR = Path(__file__).resolve().parents[2] / "seed" / "ui_labels"
NON_ENGLISH_LOCALES = ["ar", "de", "es", "fr", "hi", "ja", "ko", "pt-BR", "ru", "zh-CN"]

# Some words are legitimately identical in certain locales (cognates/loanwords).
ALLOWED_ENGLISH_COLLISIONS: dict[str, set[str]] = {
    "es": {"user_management.status.no"},
}


def _read_locale(locale: str) -> dict[str, str]:
    with (SEED_DIR / f"{locale}.json").open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(k): str(v) for k, v in data.items()}


@pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
def test_non_english_seed_files_have_key_parity_with_english(locale: str) -> None:
    english = _read_locale("en")
    target = _read_locale(locale)

    missing = sorted(set(english) - set(target))
    extra = sorted(set(target) - set(english))

    assert missing == []
    assert extra == []


@pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
def test_non_english_seed_files_do_not_contain_untranslated_english(locale: str) -> None:
    english = _read_locale("en")
    target = _read_locale(locale)
    allowed = ALLOWED_ENGLISH_COLLISIONS.get(locale, set())

    untranslated = [
        key
        for key, value in target.items()
        if key in english and english[key] == value and key not in allowed
    ]

    assert untranslated == []
