from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.system_settings import SystemSettings
from services.bootstrap import SINGLETON_KEY, normalize_supported_locales
from utils.db import AsyncSessionLocal


def _mask_secret(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return "***...***"


async def get_system_settings_row(
    session: AsyncSession,
    create_if_missing: bool = True,
) -> SystemSettings | None:
    query = (
        select(SystemSettings)
        .where(
            SystemSettings.singleton_key == SINGLETON_KEY,
            SystemSettings.deleted_at.is_(None),
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


async def get_site_name_from_db() -> str | None:
    async with AsyncSessionLocal() as session:
        settings = await get_system_settings_row(session=session, create_if_missing=False)
        if settings is None:
            return None
        if settings.site_name and settings.site_name.strip():
            return settings.site_name.strip()
        return None


async def get_provider_api_key_from_db(provider: str) -> str | None:
    async with AsyncSessionLocal() as session:
        settings = await get_system_settings_row(session=session, create_if_missing=False)
        key = None
        if settings is not None:
            if provider == "openai":
                key = settings.openai_api_key
            elif provider == "deepseek":
                key = settings.deepseek_api_key
            if key and key.strip():
                return key.strip()

        # Legacy compatibility: allow provider keys from env when DB is not configured.
        env_var = None
        if provider == "openai":
            env_var = "OPENAI_API_KEY"
        elif provider == "deepseek":
            env_var = "DEEPSEEK_API_KEY"

        if env_var:
            env_key = os.getenv(env_var)
            if env_key and env_key.strip():
                return env_key.strip()

        return None


def masked(value: str | None) -> str | None:
    return _mask_secret(value)


def normalize_locales(default_locale: str, supported_locales: list[str]) -> tuple[str, list[str]]:
    return normalize_supported_locales(
        default_locale=default_locale,
        supported_locales=supported_locales,
    )
