from __future__ import annotations

import re
import secrets

from settings import INITIAL_SETUP_TOKEN
from utils.password_validator import validate_password_strength

from services.ui_label_seed import list_seed_locales


_LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,8}([_-][A-Za-z]{2,8})?$")


class BootstrapError(Exception):
    pass


class SetupMisconfiguredError(BootstrapError):
    pass


class InvalidSetupTokenError(BootstrapError):
    pass


class AlreadyInitializedError(BootstrapError):
    pass


class SetupValidationError(BootstrapError):
    pass


def normalize_locale(locale: str) -> str:
    normalized = locale.strip().replace("_", "-")
    if not _LOCALE_PATTERN.match(normalized):
        raise SetupValidationError(f"Invalid locale format: {locale}")
    return normalized


def normalize_supported_locales(
    default_locale: str,
    supported_locales: list[str],
) -> tuple[str, list[str]]:
    normalized_default = normalize_locale(default_locale)

    normalized_supported: list[str] = []
    for locale in supported_locales:
        normalized = normalize_locale(locale)
        if normalized not in normalized_supported:
            normalized_supported.append(normalized)

    if normalized_default not in normalized_supported:
        raise SetupValidationError(
            "default_locale must be included in supported_locales"
        )

    return normalized_default, normalized_supported


def merged_supported_locales(locales: list[str]) -> list[str]:
    return list(dict.fromkeys([*locales, *list_seed_locales()]))


def validate_setup_token(provided_token: str) -> None:
    if not INITIAL_SETUP_TOKEN:
        raise SetupMisconfiguredError("INITIAL_SETUP_TOKEN is not configured")

    if not secrets.compare_digest(provided_token, INITIAL_SETUP_TOKEN):
        raise InvalidSetupTokenError("Invalid setup token")


def validate_password(password: str) -> None:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise SetupValidationError(
            f"Password does not meet requirements: {', '.join(errors)}"
        )


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def validate_email_settings_input(data) -> None:
    smtp_host = normalize_optional(data.smtp_host)
    smtp_from_email = normalize_optional(data.smtp_from_email)
    has_core = bool(smtp_host or data.smtp_port or smtp_from_email)
    if not has_core:
        return
    if not smtp_host or not data.smtp_port or not smtp_from_email:
        raise SetupValidationError(
            "smtp_host, smtp_port and smtp_from_email are required when email settings are provided"
        )
