# /backend/services/bootstrap.py

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from models.system_settings import SystemSettings
from models.user import User
from services.bootstrap_state import create_initial_admin
from services.bootstrap_state import finalize_bootstrap
from services.bootstrap_state import get_system_settings
from services.bootstrap_state import persist_initialized_settings
from services.bootstrap_state import rollback_and_raise_already_initialized
from services.bootstrap_state import rollback_and_raise_validation_failed
from services.bootstrap_validation import AlreadyInitializedError as _AlreadyInitializedError
from services.bootstrap_validation import BootstrapError as _BootstrapError
from services.bootstrap_validation import InvalidSetupTokenError as _InvalidSetupTokenError
from services.bootstrap_validation import SetupMisconfiguredError as _SetupMisconfiguredError
from services.bootstrap_validation import SetupValidationError as _SetupValidationError
from services.bootstrap_validation import merged_supported_locales
from services.bootstrap_validation import normalize_supported_locales
from services.bootstrap_validation import validate_email_settings_input
from services.bootstrap_validation import validate_password
from services.bootstrap_validation import validate_setup_token


_INITIALIZATION_LOCK = asyncio.Lock()
SINGLETON_KEY = "default"
AlreadyInitializedError = _AlreadyInitializedError
BootstrapError = _BootstrapError
InvalidSetupTokenError = _InvalidSetupTokenError
SetupMisconfiguredError = _SetupMisconfiguredError
SetupValidationError = _SetupValidationError

__all__ = [
    "AlreadyInitializedError",
    "BootstrapError",
    "BootstrapInput",
    "InvalidSetupTokenError",
    "SINGLETON_KEY",
    "SetupMisconfiguredError",
    "SetupValidationError",
    "get_system_settings",
    "initialize_application",
    "is_initialized",
    "normalize_supported_locales",
]


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

async def is_initialized(session: AsyncSession) -> bool:
    settings = await get_system_settings(session=session)
    return bool(settings and settings.is_initialized)

async def _create_initial_admin(
    session: AsyncSession,
    admin_email: str,
    admin_password: str,
) -> User:
    return await create_initial_admin(
        session=session,
        admin_email=admin_email,
        admin_password=admin_password,
    )


async def initialize_application(
    session: AsyncSession,
    data: BootstrapInput,
) -> tuple[SystemSettings, User]:
    validate_setup_token(data.setup_token)
    validate_password(data.admin_password)
    validate_email_settings_input(data)
    default_locale, supported_locales = normalize_supported_locales(
        default_locale=data.default_locale,
        supported_locales=merged_supported_locales(data.supported_locales),
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

            await persist_initialized_settings(
                session=session,
                settings=settings,
                data=data,
                default_locale=default_locale,
                supported_locales=supported_locales,
            )

            return await finalize_bootstrap(
                session=session,
                settings=settings,
                admin_user=admin_user,
            )

        except (IntegrityError,) as exc:
            await rollback_and_raise_already_initialized(session, exc)
        except (OperationalError,) as exc:
            await rollback_and_raise_already_initialized(session, exc)

        except (BootstrapError,):
            await session.rollback()
            raise

        except Exception as exc:
            await rollback_and_raise_validation_failed(session, exc)
