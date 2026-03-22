# /frontend/tests/test_setup_initialization_e2e.py

import os
import re

import pytest
from playwright.sync_api import expect
from backend.tests.test_env import TEST_INITIAL_SETUP_TOKEN

from frontend.tests.conftest import FAST_API_BASE_URL, FRONTEND_BASE_URL
from frontend.tests.state_helpers import (
    SeedUser,
    read_system_settings,
    reset_uninitialized_state,
    seed_initialized_state,
    seed_ui_locales,
)


SETUP_TOKEN = os.environ.get("INITIAL_SETUP_TOKEN", TEST_INITIAL_SETUP_TOKEN)


def _login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND_BASE_URL}/login")
    expect(page.get_by_label("email")).to_be_visible()
    expect(page.get_by_label("password")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()
    page.get_by_label("email").fill(email)
    page.get_by_label("password").fill(password)
    page.locator("button[type='submit']").click()


def _authenticate_as_seeded_user(page, email: str, password: str) -> None:
    _login(page, email, password)
    expect(page).to_have_url(re.compile(".*/dashboard$"))


def _complete_setup_and_reach_login(page) -> None:
    with page.expect_response(re.compile(r".*/setup$")) as response_info:
        page.get_by_role("button", name="Initialize application").click()
    response = response_info.value
    assert response.ok, response.text()

    status_response = page.request.get(f"{FAST_API_BASE_URL}/setup/status")
    assert status_response.status == 200
    assert status_response.json()["is_initialized"] is True

    try:
        expect(page).to_have_url(re.compile(".*/login$"), timeout=10000)
        return
    except AssertionError:
        expect(page.get_by_text("Application Already Configured")).to_be_visible()
        page.get_by_role("link", name="Go to login").click()
        expect(page).to_have_url(re.compile(".*/login$"))


def test_first_run_setup_journey(visual_page):
    reset_uninitialized_state()

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/setup")
    snap("setup_initial")

    expect(page.get_by_text("First-Run Setup")).to_be_visible()

    page.get_by_label("Initial setup token").fill(SETUP_TOKEN)
    page.get_by_label("Site name").fill("E2E Setup Site")
    page.get_by_label("Admin email").fill("e2e-admin@example.com")
    page.get_by_label("Admin password").fill("SetupAdminPass123!")
    snap("setup_form_filled")
    _complete_setup_and_reach_login(page)
    snap("post_setup_login")

    page.goto(f"{FRONTEND_BASE_URL}/setup")
    expect(page.get_by_text("Application Already Configured")).to_be_visible()
    snap("setup_already_configured")

    response = page.request.get(f"{FAST_API_BASE_URL}/setup/status")
    assert response.status == 200
    assert response.json()["is_initialized"] is True


@pytest.mark.ui_locale("fr-FR")
def test_setup_page_auto_switches_copy_from_browser_locale(visual_page):
    reset_uninitialized_state()

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/setup")
    snap("setup_fr_locale")
    expect(page.get_by_role("heading", name="Configuration initiale")).to_be_visible()


def test_admin_settings_has_no_default_locale_selector_and_saves_supported_locales(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        users=[
            SeedUser(
                full_name="E2E Admin",
                email="e2e-admin@example.com",
                password="SetupAdminPass123!",
                is_admin=True,
            )
        ]
    )

    page, snap = visual_page

    _authenticate_as_seeded_user(page, "e2e-admin@example.com", "SetupAdminPass123!")
    page.goto(f"{FRONTEND_BASE_URL}/admin/settings")
    expect(page.get_by_text("Admin settings")).to_be_visible()
    snap("admin_settings_initial")

    # Default-locale chips were removed from Admin settings UI.
    assert page.get_by_role("button", name="ru", exact=True).count() == 0

    page.get_by_label("Supported locales").fill("ru, en")
    snap("admin_supported_locales_changed")

    page.locator("form button[type='submit']").click()
    expect(page.locator("form button[type='submit']")).to_be_visible()
    snap("admin_settings_saved")

    settings = read_system_settings()
    assert settings is not None
    assert settings.default_locale == "ru"
    assert "ru" in settings.supported_locales


def test_mobile_first_setup_and_login_visuals(visual_page):
    reset_uninitialized_state()

    page, snap = visual_page

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{FRONTEND_BASE_URL}/setup")
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
    _complete_setup_and_reach_login(page)

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{FRONTEND_BASE_URL}/login")
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("login_mobile")

    page.set_viewport_size({"width": 1728, "height": 1117})
    page.reload()
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("login_desktop")


def test_selecting_ar_locale_switches_document_to_rtl_visual(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        users=[
            SeedUser(
                full_name="E2E Admin",
                email="e2e-admin@example.com",
                password="SetupAdminPass123!",
                is_admin=True,
            )
        ]
    )
    seed_ui_locales(["en", "ar"])

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/login")
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
