import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import api.admin_settings as admin_settings_api
from auth.auth_handler import create_access_token
from models.system_settings import SystemSettings
from models.ui_label import UiLabel
from models.ui_locale import UiLocale
from tests.helper import create_test_user
from utils.password import verify_password


@pytest.mark.asyncio
async def test_admin_settings_requires_auth(client: AsyncClient):
    response = await client.get("/admin/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_settings_requires_admin(client: AsyncClient, session: AsyncSession):
    user = await create_test_user(session=session, email="user@example.com")
    token = create_access_token(data={"sub": user.email})
    response = await client.get(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


@pytest.mark.asyncio
async def test_admin_settings_get_and_update(client: AsyncClient, session: AsyncSession):
    admin = await create_test_user(session=session, email="admin@example.com")
    admin.is_superuser = True
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    token = create_access_token(data={"sub": admin.email})

    get_resp = await client.get(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["admin_email"] == "admin@example.com"
    assert get_resp.json()["openai_api_key_masked"] is None
    assert get_resp.json()["auth_frontend_base_url"] is None
    assert get_resp.json()["auth_backend_base_url"] is None

    update_resp = await client.put(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "site_name": "Configured Site",
            "default_locale": "en",
            "supported_locales": ["en", "fr"],
            "openai_api_key": "openai_test_key_placeholder",
            "deepseek_api_key": "deepseek_test_key_placeholder",
            "admin_email": "new-admin@example.com",
            "admin_password": "StrongAdminPass123!",
            "site_logo": "data:image/png;base64,abc",
            "background_image": "data:image/png;base64,def",
            "auth_frontend_base_url": "https://app.example.com",
            "auth_backend_base_url": "https://api.example.com",
        },
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["site_name"] == "Configured Site"
    assert body["supported_locales"] == ["en", "fr"]
    assert body["admin_email"] == "new-admin@example.com"
    assert body["openai_api_key_masked"] is not None
    assert body["deepseek_api_key_masked"] is not None
    assert body["email_configured"] is False
    assert body["auth_frontend_base_url"] == "https://app.example.com"
    assert body["auth_backend_base_url"] == "https://api.example.com"

    settings_result = await session.execute(
        select(SystemSettings).where(SystemSettings.singleton_key == "default")
    )
    settings = settings_result.scalars().first()
    assert settings is not None
    assert settings.site_name == "Configured Site"
    assert settings.default_locale == "en"
    assert settings.supported_locales == ["en", "fr"]
    assert settings.openai_api_key == "openai_test_key_placeholder"
    assert settings.deepseek_api_key == "deepseek_test_key_placeholder"
    assert settings.site_logo == "data:image/png;base64,abc"
    assert settings.background_image == "data:image/png;base64,def"
    assert settings.auth_frontend_base_url == "https://app.example.com"
    assert settings.auth_backend_base_url == "https://api.example.com"

    await session.refresh(admin)
    assert admin.email == "new-admin@example.com"
    assert verify_password("StrongAdminPass123!", admin.hashed_password)


@pytest.mark.asyncio
async def test_admin_email_settings_check(client: AsyncClient, session: AsyncSession, monkeypatch):
    admin = await create_test_user(session=session, email="admin-check@example.com")
    admin.is_superuser = True
    session.add(admin)
    await session.commit()

    token = create_access_token(data={"sub": admin.email})

    called = {"count": 0}

    def _fake_test_connection(_config):
        called["count"] += 1

    monkeypatch.setattr(admin_settings_api, "test_smtp_connection", _fake_test_connection)

    response = await client.post(
        "/admin/settings/email/check",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user",
            "smtp_password": "pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_use_tls": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_admin_settings_update_seeds_custom_supported_locale(
    client: AsyncClient,
    session: AsyncSession,
):
    admin = await create_test_user(session=session, email="admin-locales@example.com")
    admin.is_superuser = True
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    token = create_access_token(data={"sub": admin.email})

    response = await client.put(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "default_locale": "sk",
            "supported_locales": ["en", "sk"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["default_locale"] == "sk"
    assert body["supported_locales"] == ["en", "sk"]

    locales_result = await session.execute(select(UiLocale))
    locales = {row.locale for row in locales_result.scalars().all()}
    assert "en" in locales
    assert "sk" in locales

    labels_result = await session.execute(select(UiLabel).where(UiLabel.locale == "sk"))
    sk_labels = list(labels_result.scalars().all())
    assert sk_labels == []


@pytest.mark.asyncio
async def test_admin_settings_supported_locales_without_default_uses_first_locale(
    client: AsyncClient,
    session: AsyncSession,
):
    admin = await create_test_user(session=session, email="admin-locales-first@example.com")
    admin.is_superuser = True
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    token = create_access_token(data={"sub": admin.email})

    response = await client.put(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "supported_locales": ["fr", "en"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["default_locale"] == "fr"
    assert body["supported_locales"] == ["fr", "en"]
