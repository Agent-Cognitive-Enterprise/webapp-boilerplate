# /backend/tests/api/test_setup.py

import asyncio
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

import api.setup as setup_api
from i18n.messages import get_message
from main import app
from models.system_settings import SystemSettings
from models.ui_label import UiLabel
from models.ui_locale import UiLocale
from models.user import User
from services import bootstrap
from services.bootstrap import get_system_settings
from utils.db import get_session

SETUP_TOKEN = "test-initial-setup-token"


@pytest_asyncio.fixture
async def setup_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.pop(get_session, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_setup_status_reports_uninitialized(setup_env):
    client, _ = setup_env
    response = await client.get("/setup/status")

    assert response.status_code == 200
    assert response.json()["is_initialized"] is False
    assert "en" in response.json()["seed_locales"]


@pytest.mark.asyncio
async def test_setup_status_exposes_non_secret_email_defaults_from_env_when_uninitialized(
    setup_env,
    monkeypatch,
):
    client, _ = setup_env
    monkeypatch.setenv("SMTP_HOST", "smtp.env.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("AUTH_FRONTEND_BASE_URL", "https://app.env.example.com")
    monkeypatch.setenv("AUTH_BACKEND_BASE_URL", "https://api.env.example.com")

    response = await client.get("/setup/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_initialized"] is False
    assert payload["email_defaults"] == {
        "smtp_host": "smtp.env.example.com",
        "smtp_port": 587,
        "smtp_username": "smtp-user",
        "smtp_from_email": "noreply@example.com",
        "smtp_use_tls": True,
        "auth_frontend_base_url": "https://app.env.example.com",
        "auth_backend_base_url": "https://api.env.example.com",
    }
    assert "smtp_password" not in payload["email_defaults"]


@pytest.mark.asyncio
async def test_setup_email_check_returns_localized_message(setup_env):
    client, _ = setup_env
    response = await client.post(
        "/setup/email/check",
        json={},
        headers={"Accept-Language": "fr-FR"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == get_message(
        key="common.email_settings_required_fields",
        locale="fr",
        default="smtp_host, smtp_port and smtp_from_email are required",
    )


@pytest.mark.asyncio
async def test_setup_success_creates_settings_and_admin(setup_env, monkeypatch):
    client, session_factory = setup_env
    for env_key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_USE_TLS",
        "AUTH_FRONTEND_BASE_URL",
        "AUTH_BACKEND_BASE_URL",
    ):
        monkeypatch.delenv(env_key, raising=False)

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en", "fr"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_initialized"] is True
    assert payload["site_name"] == "ACE Cloud"
    assert payload["default_locale"] == "en"
    assert "en" in payload["supported_locales"]
    assert "fr" in payload["supported_locales"]
    assert "de" in payload["supported_locales"]
    assert payload["admin_email"] == "admin@example.com"
    assert payload["email_configured"] is False

    async with session_factory() as session:
        settings_result = await session.execute(select(SystemSettings))
        settings = settings_result.scalars().first()
        assert settings is not None
        assert settings.is_initialized is True
        assert settings.site_name == "ACE Cloud"
        assert settings.auth_frontend_base_url is None
        assert settings.auth_backend_base_url is None

        user_result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin_user = user_result.scalars().first()
        assert admin_user is not None
        assert admin_user.is_superuser is True
        assert admin_user.is_active is True

        locale_result = await session.execute(select(UiLocale).where(UiLocale.locale == "fr"))
        fr_locale = locale_result.scalars().first()
        assert fr_locale is not None
        assert len(fr_locale.values_hash) > 0

        fr_label_result = await session.execute(
            select(UiLabel).where(
                UiLabel.locale == "fr",
                UiLabel.key == "setup.title.first_run_setup",
            )
        )
        fr_label = fr_label_result.scalars().first()
        assert fr_label is not None
        assert fr_label.value == "Configuration initiale"

    status_after_setup = await client.get("/setup/status")
    assert status_after_setup.status_code == 200
    assert status_after_setup.json()["email_defaults"] is None


@pytest.mark.asyncio
async def test_setup_sends_admin_welcome_email_when_smtp_is_provided(setup_env, monkeypatch):
    client, _ = setup_env
    sent: dict[str, Any] = {}

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        sent["config"] = config
        sent["to_email"] = to_email
        sent["subject"] = subject
        sent["body_text"] = body_text

    monkeypatch.setattr(setup_api, "send_email", _capture_email)

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "smtp-pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
            "auth_frontend_base_url": "https://app.example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["email_configured"] is True
    assert sent["to_email"] == "admin@example.com"
    assert sent["subject"] == "ACE Cloud is live"
    assert "Your site 'ACE Cloud' is live now." in str(sent["body_text"])
    assert "https://app.example.com/admin/settings" in str(sent["body_text"])
    assert "Thank you," in str(sent["body_text"])
    assert "Site Automation" in str(sent["body_text"])
    assert sent["config"].host == "smtp.example.com"
    assert sent["config"].port == 587
    assert sent["config"].username == "smtp-user"
    assert sent["config"].password == "smtp-pass"
    assert sent["config"].from_email == "noreply@example.com"
    assert sent["config"].use_tls is True


@pytest.mark.asyncio
async def test_setup_uses_env_smtp_defaults_and_sends_admin_welcome_email(setup_env, monkeypatch):
    client, _ = setup_env
    sent: dict[str, Any] = {}

    monkeypatch.setenv("SMTP_HOST", "smtp.env.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-env-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-env-pass")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "env-noreply@example.com")
    monkeypatch.setenv("SMTP_USE_TLS", "false")

    def _capture_email(*, config, to_email: str, subject: str, body_text: str) -> None:
        sent["config"] = config
        sent["to_email"] = to_email
        sent["subject"] = subject
        sent["body_text"] = body_text

    monkeypatch.setattr(setup_api, "send_email", _capture_email)

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["email_configured"] is True
    assert sent["to_email"] == "admin@example.com"
    assert sent["subject"] == "ACE Cloud is live"
    assert "Your site 'ACE Cloud' is live now." in str(sent["body_text"])
    assert "/admin/settings" in str(sent["body_text"])
    assert "Thank you," in str(sent["body_text"])
    assert "Site Automation" in str(sent["body_text"])
    assert sent["config"].host == "smtp.env.example.com"
    assert sent["config"].port == 465
    assert sent["config"].username == "smtp-env-user"
    assert sent["config"].password == "smtp-env-pass"
    assert sent["config"].from_email == "env-noreply@example.com"
    assert sent["config"].use_tls is False


@pytest.mark.asyncio
async def test_setup_persists_auth_base_urls_in_system_settings(setup_env):
    client, session_factory = setup_env

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
            "auth_frontend_base_url": "https://app.example.com",
            "auth_backend_base_url": "https://api.example.com",
        },
    )

    assert response.status_code == 200
    async with session_factory() as session:
        settings_result = await session.execute(select(SystemSettings))
        settings = settings_result.scalars().first()
        assert settings is not None
        assert settings.auth_frontend_base_url == "https://app.example.com"
        assert settings.auth_backend_base_url == "https://api.example.com"


@pytest.mark.asyncio
async def test_setup_succeeds_even_if_welcome_email_send_fails(setup_env, monkeypatch):
    client, session_factory = setup_env

    def _fail_send_email(*_args, **_kwargs) -> None:
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(setup_api, "send_email", _fail_send_email)

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_from_email": "noreply@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["is_initialized"] is True

    async with session_factory() as session:
        settings_result = await session.execute(select(SystemSettings))
        settings = settings_result.scalars().first()
        assert settings is not None
        assert settings.is_initialized is True

@pytest.mark.asyncio
async def test_setup_rejects_invalid_payload(setup_env):
    client, _ = setup_env

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "sk",
            "supported_locales": ["en", "fr"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )

    assert response.status_code == 400
    assert "default_locale must be included" in response.json()["detail"]


@pytest.mark.asyncio
async def test_setup_rejects_missing_or_invalid_token(setup_env):
    client, _ = setup_env

    wrong_token_response = await client.post(
        "/setup",
        json={
            "setup_token": "wrong-token",
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )
    assert wrong_token_response.status_code == 401

    missing_token_response = await client.post(
        "/setup",
        json={
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )
    assert missing_token_response.status_code == 422


@pytest.mark.asyncio
async def test_setup_is_transaction_safe_on_failure(setup_env, monkeypatch):
    client, session_factory = setup_env

    async def _raise_after_validation(*args, **kwargs):
        raise bootstrap.SetupValidationError("simulated failure")

    monkeypatch.setattr(bootstrap, "_create_initial_admin", _raise_after_validation)

    response = await client.post(
        "/setup",
        json={
            "setup_token": SETUP_TOKEN,
            "site_name": "ACE Cloud",
            "default_locale": "en",
            "supported_locales": ["en"],
            "admin_email": "admin@example.com",
            "admin_password": "SetupAdminPass123!",
        },
    )

    assert response.status_code == 400

    async with session_factory() as session:
        settings = await get_system_settings(session=session, create_if_missing=False)
        assert settings is None or settings.is_initialized is False

        user_result = await session.execute(select(User))
        assert user_result.scalars().first() is None


@pytest.mark.asyncio
async def test_setup_race_condition_guarded(setup_env):
    client, session_factory = setup_env
    payload_a = {
        "setup_token": SETUP_TOKEN,
        "site_name": "ACE Cloud",
        "default_locale": "en",
        "supported_locales": ["en"],
        "admin_email": "adminA@example.com",
        "admin_password": "SetupAdminPass123!",
    }
    payload_b = {
        "setup_token": SETUP_TOKEN,
        "site_name": "ACE Cloud",
        "default_locale": "en",
        "supported_locales": ["en"],
        "admin_email": "adminB@example.com",
        "admin_password": "SetupAdminPass123!",
    }

    response_a, response_b = await asyncio.gather(
        client.post("/setup", json=payload_a),
        client.post("/setup", json=payload_b),
    )

    statuses = sorted([response_a.status_code, response_b.status_code])
    assert statuses == [200, 409]

    async with session_factory() as session:
        settings_result = await session.execute(select(SystemSettings))
        settings = settings_result.scalars().all()
        assert len(settings) == 1
        assert settings[0].is_initialized is True

        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        assert len(users) == 1
