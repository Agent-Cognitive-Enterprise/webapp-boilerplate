from __future__ import annotations

from datetime import datetime, timezone
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from models.system_settings import SystemSettings
from models.user import User
from services.bootstrap_validation import AlreadyInitializedError
from services.bootstrap_validation import SetupValidationError
from services.bootstrap_validation import normalize_optional
from services.ui_label_seed import seed_ui_labels_for_locales
from utils.password import get_password_hash


SINGLETON_KEY = "default"


async def get_system_settings(
    session: AsyncSession,
    create_if_missing: bool = False,
) -> SystemSettings | None:
    query = (
        select(SystemSettings)
        .where(
            SystemSettings.singleton_key == SINGLETON_KEY,
            col(SystemSettings.deleted_at).is_(None),
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


async def create_initial_admin(
    session: AsyncSession,
    admin_email: str,
    admin_password: str,
) -> User:
    existing_user_query = (
        select(User)
        .where(
            User.email == admin_email,
            col(User.deleted_at).is_(None),
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


async def persist_initialized_settings(
    *,
    session: AsyncSession,
    settings: SystemSettings,
    data,
    default_locale: str,
    supported_locales: list[str],
) -> None:
    settings.site_name = data.site_name.strip()
    settings.default_locale = default_locale
    settings.supported_locales = supported_locales
    settings.smtp_host = normalize_optional(data.smtp_host)
    settings.smtp_port = data.smtp_port
    settings.smtp_username = normalize_optional(data.smtp_username)
    settings.smtp_password = normalize_optional(data.smtp_password)
    settings.smtp_from_email = normalize_optional(data.smtp_from_email)
    settings.smtp_use_tls = bool(data.smtp_use_tls)
    settings.auth_frontend_base_url = normalize_optional(data.auth_frontend_base_url)
    settings.auth_backend_base_url = normalize_optional(data.auth_backend_base_url)
    settings.is_initialized = True
    settings.initialized_at = datetime.now(timezone.utc)
    session.add(settings)

    await seed_ui_labels_for_locales(
        session=session,
        locales=supported_locales,
    )


async def finalize_bootstrap(
    *,
    session: AsyncSession,
    settings: SystemSettings,
    admin_user: User,
) -> tuple[SystemSettings, User]:
    await session.commit()
    await session.refresh(settings)
    await session.refresh(admin_user)
    return settings, admin_user


async def rollback_and_raise_already_initialized(
    session: AsyncSession,
    exc: Exception,
) -> NoReturn:
    await session.rollback()
    raise AlreadyInitializedError("Application already initialized") from exc


async def rollback_and_raise_validation_failed(
    session: AsyncSession,
    exc: Exception,
) -> NoReturn:
    await session.rollback()
    raise SetupValidationError("Initialization failed") from exc
