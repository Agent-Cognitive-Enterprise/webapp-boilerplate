import re

from playwright.sync_api import expect

from frontend.tests.conftest import FRONTEND_BASE_URL
from frontend.tests.state_helpers import SeedUser, reset_uninitialized_state, seed_initialized_state


def _login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND_BASE_URL}/login")
    page.get_by_label("email").fill(email)
    page.get_by_label("password").fill(password)
    page.locator("button[type='submit']").click()


def test_unauthenticated_user_is_redirected_from_protected_route(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(site_name="E2E Protected Route Site")

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/dashboard")

    expect(page).to_have_url(re.compile(".*/login$"))
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("protected_route_redirect_to_login")


def test_login_profile_logout_journey(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Auth Journey Site",
        users=[
            SeedUser(
                full_name="E2E User",
                email="e2e-user@example.com",
                password="UserPass123!",
            )
        ],
    )

    page, snap = visual_page

    _login(page, "e2e-user@example.com", "UserPass123!")

    expect(page).to_have_url(re.compile(".*/dashboard$"))
    expect(page.get_by_text("e2e-user@example.com")).to_be_visible()
    snap("dashboard_after_login")

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    expect(page).to_have_url(re.compile(".*/profile$"))
    expect(page.get_by_text("e2e-user@example.com")).to_be_visible()
    snap("profile_after_login")

    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*/login$"))
    expect(page.get_by_role("button", name="Login")).to_be_visible()
    snap("login_after_logout")

    page.goto(f"{FRONTEND_BASE_URL}/dashboard")
    expect(page).to_have_url(re.compile(".*/login$"))
    snap("protected_route_after_logout")


def test_admin_supported_locale_change_is_visible_on_login_page(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Locale Expansion Site",
        users=[
            SeedUser(
                full_name="E2E Admin",
                email="e2e-admin@example.com",
                password="SetupAdminPass123!",
                is_admin=True,
            )
        ],
    )

    page, snap = visual_page

    _login(page, "e2e-admin@example.com", "SetupAdminPass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{FRONTEND_BASE_URL}/admin/settings")
    expect(page.get_by_text("Admin settings")).to_be_visible()
    page.get_by_label("Supported locales").fill("en, fr")
    page.get_by_role("button", name="Save settings").click()
    expect(page).to_have_url(re.compile(".*/admin/settings$"))
    snap("admin_settings_after_locale_save")

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*/login$"))

    page.get_by_text("English").click()
    expect(page.get_by_role("button", name=re.compile("Fran", re.IGNORECASE))).to_be_visible()
    snap("login_locale_selector_after_admin_update")
