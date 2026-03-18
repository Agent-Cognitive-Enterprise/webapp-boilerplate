from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlmodel import select

from auth.auth_handler import create_access_token
from frontend.tests.conftest import run_async_safely
from models.system_settings import SystemSettings
from models.ui_label import UiLabel
from models.ui_locale import UiLocale
from models.user import User
from services.ui_label_seed import seed_ui_labels_for_locales
from utils.db import get_session
from utils.password import get_password_hash


@dataclass(frozen=True)
class SeedUser:
    full_name: str
    email: str
    password: str
    is_admin: bool = False


@dataclass(frozen=True)
class SeedEmailSettings:
    smtp_host: str
    smtp_port: int
    smtp_from_email: str
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    auth_frontend_base_url: str | None = None
    auth_backend_base_url: str | None = None


def reset_uninitialized_state() -> None:
    async def _task():
        async for session in get_session():
            await session.execute(delete(UiLabel))
            await session.execute(delete(UiLocale))
            await session.execute(delete(User))
            await session.execute(delete(SystemSettings))
            await session.commit()

    run_async_safely(_task())


def seed_initialized_state(
    site_name: str = "E2E Locale Site",
    supported_locales: list[str] | None = None,
    users: list[SeedUser] | None = None,
    email_settings: SeedEmailSettings | None = None,
) -> None:
    async def _task():
        async for session in get_session():
            session.add(
                SystemSettings(
                    singleton_key="default",
                    site_name=site_name,
                    default_locale="en",
                    supported_locales=supported_locales or ["en"],
                    is_initialized=True,
                    initialized_at=datetime.now(timezone.utc),
                    smtp_host=email_settings.smtp_host if email_settings else None,
                    smtp_port=email_settings.smtp_port if email_settings else None,
                    smtp_username=email_settings.smtp_username if email_settings else None,
                    smtp_password=email_settings.smtp_password if email_settings else None,
                    smtp_from_email=(
                        email_settings.smtp_from_email if email_settings else None
                    ),
                    smtp_use_tls=email_settings.smtp_use_tls if email_settings else True,
                    auth_frontend_base_url=(
                        email_settings.auth_frontend_base_url if email_settings else None
                    ),
                    auth_backend_base_url=(
                        email_settings.auth_backend_base_url if email_settings else None
                    ),
                )
            )
            for user in users or []:
                session.add(
                    User(
                        full_name=user.full_name,
                        email=user.email,
                        hashed_password=get_password_hash(user.password),
                        is_active=True,
                        is_superuser=user.is_admin,
                        email_verified=True,
                    )
                )
            await session.commit()

    run_async_safely(_task())


def seed_ui_locales(locales: list[str]) -> None:
    async def _task():
        async for session in get_session():
            await seed_ui_labels_for_locales(
                session=session,
                locales=locales,
            )
            await session.commit()

    run_async_safely(_task())


def read_system_settings() -> SystemSettings | None:
    async def _task():
        async for session in get_session():
            result = await session.execute(
                select(SystemSettings).where(SystemSettings.singleton_key == "default")
            )
            return result.scalars().first()

    return run_async_safely(_task())


def create_test_access_token(email: str) -> str:
    return create_access_token(data={"sub": email})
