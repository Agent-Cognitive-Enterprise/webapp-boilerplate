# /backend/services/bootstrap.py

from __future__ import annotations

import asyncio
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.system_settings import SystemSettings
from models.user import User
from settings import INITIAL_SETUP_TOKEN
from services.ui_label_seed import list_seed_locales, seed_ui_labels_for_locales
from utils.password import get_password_hash
from utils.password_validator import validate_password_strength


SINGLETON_KEY = "default"
_LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,8}([_-][A-Za-z]{2,8})?$")
_INITIALIZATION_LOCK = asyncio.Lock()


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


@dataclass
class BootstrapInput:
    setup_token: str
    site_name: str
    default_locale: str
    supported_locales: list[str]
    admin_email: str
    admin_password: str
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    auth_frontend_base_url: str | None = None
    auth_backend_base_url: str | None = None


async def get_system_settings(
    session: AsyncSession,
    create_if_missing: bool = False,
) -> SystemSettings | None:
    query = (
        select(SystemSettings)
        .where(
            SystemSettings.singleton_key == SINGLETON_KEY,
            SystemSettings.deleted_at == None,
        )
        .limit(1)
    )
    result = await session.execute(query)
    settings = result.scalars().first()

    if settings is None and create_if_missing:
        settings = SystemSettings(singleton_key=SINGLETON_KEY)
        session.add(settings)
        await session.flush()

    return settings


async def is_initialized(session: AsyncSession) -> bool:
    settings = await get_system_settings(session=session)
    return bool(settings and settings.is_initialized)


def _normalize_locale(locale: str) -> str:
    normalized = locale.strip().replace("_", "-")
    if not _LOCALE_PATTERN.match(normalized):
        raise SetupValidationError(f"Invalid locale format: {locale}")
    return normalized


def normalize_supported_locales(
    default_locale: str,
    supported_locales: list[str],
) -> tuple[str, list[str]]:
    normalized_default = _normalize_locale(default_locale)

    normalized_supported: list[str] = []
    for locale in supported_locales:
        normalized = _normalize_locale(locale)
        if normalized not in normalized_supported:
            normalized_supported.append(normalized)

    if normalized_default not in normalized_supported:
        raise SetupValidationError(
            "default_locale must be included in supported_locales"
        )

    return normalized_default, normalized_supported


def _validate_setup_token(provided_token: str) -> None:
    if not INITIAL_SETUP_TOKEN:
        raise SetupMisconfiguredError("INITIAL_SETUP_TOKEN is not configured")

    if not secrets.compare_digest(provided_token, INITIAL_SETUP_TOKEN):
        raise InvalidSetupTokenError("Invalid setup token")


def _validate_password(password: str) -> None:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise SetupValidationError(
            f"Password does not meet requirements: {', '.join(errors)}"
        )


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _validate_email_settings_input(data: BootstrapInput) -> None:
    smtp_host = _normalize_optional(data.smtp_host)
    smtp_from_email = _normalize_optional(data.smtp_from_email)
    has_core = bool(smtp_host or data.smtp_port or smtp_from_email)
    if not has_core:
        return
    if not smtp_host or not data.smtp_port or not smtp_from_email:
        raise SetupValidationError(
            "smtp_host, smtp_port and smtp_from_email are required when email settings are provided"
        )


async def _create_initial_admin(
    session: AsyncSession,
    admin_email: str,
    admin_password: str,
) -> User:
    existing_user_query = (
        select(User)
        .where(
            User.email == admin_email,
            User.deleted_at == None,
        )
        .limit(1)
    )
    existing_user_result = await session.execute(existing_user_query)
    existing_user = existing_user_result.scalars().first()
    if existing_user is not None:
        raise SetupValidationError("Admin email already exists")

    admin_user = User(
        full_name="Administrator",
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        is_active=True,
        is_superuser=True,
    )
    session.add(admin_user)
    await session.flush()
    return admin_user


async def initialize_application(
    session: AsyncSession,
    data: BootstrapInput,
) -> tuple[SystemSettings, User]:
    _validate_setup_token(data.setup_token)
    _validate_password(data.admin_password)
    _validate_email_settings_input(data)
    merged_supported_locales = list(dict.fromkeys([*data.supported_locales, *list_seed_locales()]))
    default_locale, supported_locales = normalize_supported_locales(
        default_locale=data.default_locale,
        supported_locales=merged_supported_locales,
    )

    async with _INITIALIZATION_LOCK:
        try:
            settings = await get_system_settings(session=session, create_if_missing=True)
            if settings is None:
                raise SetupValidationError("Unable to load system settings")

            if settings.is_initialized:
                raise AlreadyInitializedError("Application already initialized")

            admin_user = await _create_initial_admin(
                session=session,
                admin_email=data.admin_email,
                admin_password=data.admin_password,
            )

            settings.site_name = data.site_name.strip()
            settings.default_locale = default_locale
            settings.supported_locales = supported_locales
            settings.smtp_host = _normalize_optional(data.smtp_host)
            settings.smtp_port = data.smtp_port
            settings.smtp_username = _normalize_optional(data.smtp_username)
            settings.smtp_password = _normalize_optional(data.smtp_password)
            settings.smtp_from_email = _normalize_optional(data.smtp_from_email)
            settings.smtp_use_tls = bool(data.smtp_use_tls)
            settings.auth_frontend_base_url = _normalize_optional(data.auth_frontend_base_url)
            settings.auth_backend_base_url = _normalize_optional(data.auth_backend_base_url)
            settings.is_initialized = True
            settings.initialized_at = datetime.now(timezone.utc)
            session.add(settings)

            await seed_ui_labels_for_locales(
                session=session,
                locales=supported_locales,
            )

            await session.commit()
            await session.refresh(settings)
            await session.refresh(admin_user)
            return settings, admin_user

        except (IntegrityError,) as exc:
            await session.rollback()
            # Any integrity failure at this point indicates a concurrent setup write collision
            # (singleton settings row or another unique bootstrap artifact), so treat as
            # already-initialized to keep setup idempotent and race-safe at the API layer.
            raise AlreadyInitializedError("Application already initialized") from exc
        except (OperationalError,) as exc:
            await session.rollback()
            # SQLite can surface concurrent setup contention as operational errors
            # (e.g. database lock/transaction conflicts). Normalize to conflict.
            raise AlreadyInitializedError("Application already initialized") from exc

        except (BootstrapError,):
            await session.rollback()
            raise

        except Exception as exc:
            await session.rollback()
            raise SetupValidationError("Initialization failed") from exc
