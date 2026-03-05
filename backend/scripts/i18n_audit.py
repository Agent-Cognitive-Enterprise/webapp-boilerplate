#!/usr/bin/env python3
"""Localization sanity audit.

Reports:
1) Total unique UI label keys from `seed/ui_labels/en.json`.
2) Per-locale key parity + exact-English collisions.
3) Count of hardcoded backend API response strings (`detail=...`, `message=...`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "seed" / "ui_labels"
API_DIR = ROOT / "api"


def load_locale(locale: str) -> dict[str, str]:
    with (SEED_DIR / f"{locale}.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return {str(k): str(v) for k, v in payload.items()}


def backend_message_literals() -> list[tuple[str, str, str]]:
    pattern = re.compile(
        r"(?:detail|message)\s*=\s*([\"'])(.+?)\1",
        re.DOTALL,
    )
    findings: list[tuple[str, str, str]] = []

    for py_file in sorted(API_DIR.glob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            quote, message = match.groups()
            if quote not in {'"', "'"}:
                continue
            findings.append((py_file.name, "literal", " ".join(message.split())))

    return findings


def main() -> None:
    english = load_locale("en")
    english_keys = set(english)

    print(f"TOTAL_UI_LABEL_KEYS={len(english_keys)}")

    for locale_file in sorted(SEED_DIR.glob("*.json")):
        locale = locale_file.stem
        locale_map = load_locale(locale)
        missing = sorted(english_keys - set(locale_map))
        extra = sorted(set(locale_map) - english_keys)
        same_as_english = []
        if locale != "en":
            same_as_english = [
                key
                for key, value in locale_map.items()
                if key in english and value == english[key]
            ]

        print(
            "LOCALE="
            f"{locale} COUNT={len(locale_map)} MISSING={len(missing)} "
            f"EXTRA={len(extra)} SAME_AS_EN={len(same_as_english)}"
        )

    literals = backend_message_literals()
    print(f"BACKEND_HARDCODED_API_MESSAGE_COUNT={len(literals)}")


if __name__ == "__main__":
    main()
