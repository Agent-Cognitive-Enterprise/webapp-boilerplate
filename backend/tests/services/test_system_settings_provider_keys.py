import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import services.system_settings as system_settings_service
from services.system_settings import get_provider_api_key_from_db, get_system_settings_row


def _session_factory_for_test(session: AsyncSession):
    class _SessionCtx:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    return _SessionCtx()


@pytest.mark.asyncio
async def test_provider_key_prefers_db_over_env(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai-key")
    monkeypatch.setattr(
        system_settings_service,
        "AsyncSessionLocal",
        lambda: _session_factory_for_test(session),
    )

    settings = await get_system_settings_row(session=session, create_if_missing=True)
    assert settings is not None
    settings.openai_api_key = "db-openai-key"
    session.add(settings)
    await session.commit()

    resolved = await get_provider_api_key_from_db("openai")
    assert resolved == "db-openai-key"


@pytest.mark.asyncio
async def test_provider_key_falls_back_to_env_when_db_missing(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai-key")
    monkeypatch.setattr(
        system_settings_service,
        "AsyncSessionLocal",
        lambda: _session_factory_for_test(session),
    )

    settings = await get_system_settings_row(session=session, create_if_missing=True)
    assert settings is not None
    settings.openai_api_key = None
    session.add(settings)
    await session.commit()

    resolved = await get_provider_api_key_from_db("openai")
    assert resolved == "env-openai-key"


@pytest.mark.asyncio
async def test_provider_key_unknown_provider_returns_none(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        system_settings_service,
        "AsyncSessionLocal",
        lambda: _session_factory_for_test(session),
    )
    resolved = await get_provider_api_key_from_db("unknown-provider")
    assert resolved is None
