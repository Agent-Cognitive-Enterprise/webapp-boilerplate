# /frontend/tests/test_setup_initialization_e2e.py

import re

import pytest
from playwright.sync_api import expect
from sqlalchemy import delete
from datetime import datetime, timezone

from models.system_settings import SystemSettings
from models.ui_label import UiLabel
from models.ui_locale import UiLocale
from models.user import User
from services.ui_label_seed import seed_ui_labels_for_locales
from frontend.tests.conftest import run_async_safely
from utils.password import get_password_hash
from utils.db import get_session


BASE_URL = "http://localhost:5173"
SETUP_TOKEN = "test-initial-setup-token"


def _reset_uninitialized_state():
    async def _task():
        async for session in get_session():
            await session.execute(delete(UiLabel))
            await session.execute(delete(UiLocale))
            await session.execute(delete(User))
            await session.execute(delete(SystemSettings))
            await session.commit()

    run_async_safely(_task())


def _seed_initialized_state() -> None:
    async def _task():
        async for session in get_session():
            session.add(
                SystemSettings(
                    singleton_key="default",
                    site_name="E2E Locale Site",
                    default_locale="en",
                    supported_locales=["en"],
                    is_initialized=True,
                    initialized_at=datetime.now(timezone.utc),
                )
            )
            session.add(
                User(
                    full_name="E2E Admin",
                    email="e2e-admin@example.com",
                    hashed_password=get_password_hash("SetupAdminPass123!"),
                    is_active=True,
                    is_superuser=True,
                    email_verified=True,
                )
            )
            await session.commit()

    run_async_safely(_task())


def _seed_ui_locales(locales: list[str]) -> None:
    async def _task():
        async for session in get_session():
            await seed_ui_labels_for_locales(
                session=session,
                locales=locales,
            )
            await session.commit()

    run_async_safely(_task())


def test_first_run_setup_journey(visual_page):
    _reset_uninitialized_state()

    page, snap = visual_page

    page.goto(f"{BASE_URL}/setup")
    snap("setup_initial")

    expect(page.get_by_text("First-Run Setup")).to_be_visible()

    page.get_by_label("Initial setup token").fill(SETUP_TOKEN)
    page.get_by_label("Site name").fill("E2E Setup Site")
    page.get_by_label("Admin email").fill("e2e-admin@example.com")
    page.get_by_label("Admin password").fill("SetupAdminPass123!")
    snap("setup_form_filled")
    page.get_by_role("button", name="Initialize application").click()

    expect(page).to_have_url(re.compile(".*/login$"))
    snap("post_setup_login")

    page.goto(f"{BASE_URL}/setup")
    expect(page.get_by_text("Application Already Configured")).to_be_visible()
    snap("setup_already_configured")

    response = page.request.get("http://localhost:8000/setup/status")
    assert response.status == 200
    assert response.json()["is_initialized"] is True


@pytest.mark.ui_locale("fr-FR")
def test_setup_page_auto_switches_copy_from_browser_locale(visual_page):
    _reset_uninitialized_state()

    page, snap = visual_page

    page.goto(f"{BASE_URL}/setup")
    snap("setup_fr_locale")
    expect(page.get_by_role("heading", name="Configuration initiale")).to_be_visible()


def test_admin_settings_has_no_default_locale_selector_and_saves_supported_locales(visual_page):
    _reset_uninitialized_state()
    _seed_initialized_state()

    page, snap = visual_page

    page.goto(f"{BASE_URL}/login")
    page.get_by_label("email").fill("e2e-admin@example.com")
    page.get_by_label("password").fill("SetupAdminPass123!")
    page.locator("button[type='submit']").click()
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{BASE_URL}/admin/settings")
    expect(page.get_by_text("Admin settings")).to_be_visible()
    snap("admin_settings_initial")

    # Default-locale chips were removed from Admin settings UI.
    assert page.get_by_role("button", name="ru", exact=True).count() == 0

    page.get_by_label("Supported locales").fill("ru, en")
    snap("admin_supported_locales_changed")

    page.locator("form button[type='submit']").click()
    expect(page.locator("form button[type='submit']")).to_be_visible()
    snap("admin_settings_saved")

    saved = page.request.get("http://localhost:8000/admin/settings")
    assert saved.status == 200
    payload = saved.json()
    assert payload["default_locale"] == "ru"
    assert "ru" in payload["supported_locales"]


def test_mobile_first_setup_and_login_visuals(visual_page):
    _reset_uninitialized_state()

    page, snap = visual_page

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{BASE_URL}/setup")
    expect(page.get_by_text("First-Run Setup")).to_be_visible()
    expect(page.get_by_role("button", name="Initialize application")).to_be_visible()
    snap("setup_mobile")

    page.set_viewport_size({"width": 1728, "height": 1117})
    page.reload()
    expect(page.get_by_text("First-Run Setup")).to_be_visible()
    snap("setup_desktop")

    page.get_by_label("Initial setup token").fill(SETUP_TOKEN)
    page.get_by_label("Site name").fill("Responsive Visual Site")
    page.get_by_label("Admin email").fill("e2e-admin@example.com")
    page.get_by_label("Admin password").fill("SetupAdminPass123!")
    page.get_by_role("button", name="Initialize application").click()
    expect(page).to_have_url(re.compile(".*/login$"))

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{BASE_URL}/login")
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("login_mobile")

    page.set_viewport_size({"width": 1728, "height": 1117})
    page.reload()
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("login_desktop")


def test_selecting_ar_locale_switches_document_to_rtl_visual(visual_page):
    _reset_uninitialized_state()
    _seed_initialized_state()
    _seed_ui_locales(["en", "ar"])

    page, snap = visual_page

    page.goto(f"{BASE_URL}/login")
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    assert page.evaluate("document.documentElement.dir") == "ltr"
    snap("login_before_ar_selection_ltr")

    page.get_by_text("English").click()
    page.get_by_role("button", name=re.compile("العربية")).click()
    page.get_by_role("button", name=re.compile("save|حفظ", re.IGNORECASE)).click()

    page.wait_for_timeout(800)
    expect(page.get_by_role("button", name="تسجيل الدخول")).to_be_visible()
    assert page.evaluate("document.documentElement.lang").startswith("ar")
    assert page.evaluate("document.documentElement.dir") == "rtl"
    snap("login_after_ar_selection_rtl")
