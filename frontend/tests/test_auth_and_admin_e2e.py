import re

from playwright.sync_api import expect

from frontend.tests.conftest import FRONTEND_BASE_URL
from frontend.tests.state_helpers import (
    read_ui_label_suggestion_counts,
    SeedUser,
    reset_uninitialized_state,
    seed_initialized_state,
    seed_ui_locales,
)


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


def test_authenticated_user_can_switch_profile_locale_to_rtl(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Authenticated Locale Switch Site",
        supported_locales=["en", "ar"],
        users=[
            SeedUser(
                full_name="Locale User",
                email="locale-user@example.com",
                password="LocalePass123!",
            )
        ],
    )
    seed_ui_locales(["en", "ar"])

    page, snap = visual_page

    _login(page, "locale-user@example.com", "LocalePass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    expect(page).to_have_url(re.compile(".*/profile$"))
    expect(page.get_by_text("locale-user@example.com")).to_be_visible()
    assert page.evaluate("document.documentElement.dir") == "ltr"
    snap("profile_before_authenticated_locale_switch")

    page.get_by_text("English").click()
    page.get_by_role("button", name=re.compile("العربية")).click()
    page.get_by_role("button", name=re.compile("save|حفظ", re.IGNORECASE)).click()

    page.wait_for_timeout(800)
    expect(page).to_have_url(re.compile(".*/profile$"))
    assert page.evaluate("document.documentElement.lang").startswith("ar")
    assert page.evaluate("document.documentElement.dir") == "rtl"
    expect(page.get_by_text("العربية")).to_be_visible()
    snap("profile_after_authenticated_locale_switch_rtl")


def test_profile_locale_selection_persists_across_reload_and_relogin(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Locale Persistence Site",
        supported_locales=["en", "ar"],
        users=[
            SeedUser(
                full_name="Persistent Locale User",
                email="persistent-locale@example.com",
                password="LocalePass123!",
            )
        ],
    )
    seed_ui_locales(["en", "ar"])

    page, snap = visual_page

    _login(page, "persistent-locale@example.com", "LocalePass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    expect(page).to_have_url(re.compile(".*/profile$"))
    expect(page.get_by_text("English")).to_be_visible()

    page.get_by_text("English").click()
    page.get_by_role("button", name=re.compile("العربية")).click()
    page.get_by_role("button", name=re.compile("save|حفظ", re.IGNORECASE)).click()

    page.wait_for_timeout(800)
    expect(page.get_by_text("العربية")).to_be_visible()
    assert page.evaluate("window.localStorage.getItem('uiLocale')") == "ar"
    snap("profile_locale_after_selection")

    page.reload()
    expect(page).to_have_url(re.compile(".*/profile$"))
    expect(page.get_by_text("العربية")).to_be_visible()
    assert page.evaluate("document.documentElement.lang").startswith("ar")
    assert page.evaluate("document.documentElement.dir") == "rtl"
    snap("profile_locale_after_reload")

    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*/login$"))
    expect(page.get_by_text("العربية")).to_be_visible()
    snap("login_locale_after_logout")

    page.locator('input[name="email"]').fill("persistent-locale@example.com")
    page.locator('input[name="password"]').fill("LocalePass123!")
    page.locator("button[type='submit']").click()
    expect(page).to_have_url(re.compile(".*/dashboard$"))
    assert page.evaluate("window.localStorage.getItem('uiLocale')") == "ar"
    assert page.evaluate("document.documentElement.lang").startswith("ar")
    assert page.evaluate("document.documentElement.dir") == "rtl"
    snap("dashboard_locale_after_relogin")


def test_authenticated_user_can_submit_ui_label_suggestion(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E UiLabel Suggestion Site",
        users=[
            SeedUser(
                full_name="Suggestion User",
                email="suggestion-user@example.com",
                password="SuggestPass123!",
            )
        ],
    )
    seed_ui_locales(["en"])

    page, snap = visual_page

    _login(page, "suggestion-user@example.com", "SuggestPass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    heading = page.get_by_role("heading", name="User Profile")
    expect(heading).to_be_visible()

    heading.click(button="right")
    expect(page.get_by_text("Suggest translation")).to_be_visible()
    page.locator("textarea").fill("Profile Home")
    snap("ui_label_suggestion_modal_filled")
    page.get_by_role("button", name="Submit").click()

    expect(page.get_by_text("Suggest translation")).to_have_count(0)
    counts = read_ui_label_suggestion_counts("profile.title.user_profile", "en")
    assert counts.get("Profile Home") == 1
    snap("ui_label_suggestion_submitted")


def test_admin_can_create_deactivate_and_delete_user(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E User Management Site",
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

    page.goto(f"{FRONTEND_BASE_URL}/users")
    expect(page.locator('input[aria-label="user_management.field.full_name"]')).to_be_visible()

    page.locator('input[aria-label="user_management.field.full_name"]').fill("Managed Browser User")
    page.locator('input[aria-label="user_management.field.email"]').fill("managed-browser@example.com")
    page.locator('input[aria-label="user_management.field.password"]').fill("ManagedPass123!")
    snap("user_management_form_filled")
    page.locator("form").first.locator("button").click()

    managed_row = page.locator("tr", has_text="managed-browser@example.com")
    expect(managed_row).to_be_visible()
    expect(managed_row.get_by_text("Active")).to_be_visible()
    snap("user_management_after_create")

    managed_row.get_by_role("button", name="Deactivate").click()
    expect(managed_row.get_by_text("Inactive")).to_be_visible()
    expect(managed_row.get_by_role("button", name="Activate")).to_be_visible()
    snap("user_management_after_deactivate")

    page.goto(f"{FRONTEND_BASE_URL}/profile")
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*/login$"))

    _login(page, "managed-browser@example.com", "ManagedPass123!")
    expect(page.get_by_text("Invalid email or password")).to_be_visible()
    snap("managed_user_login_blocked_after_deactivate")

    _login(page, "e2e-admin@example.com", "SetupAdminPass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    page.goto(f"{FRONTEND_BASE_URL}/users")
    managed_row = page.locator("tr", has_text="managed-browser@example.com")
    managed_row.get_by_role("button", name="Delete").click()
    expect(managed_row).to_have_count(0)
    snap("user_management_after_delete")


def test_admin_email_settings_check_shows_validation_feedback(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Admin Settings Validation Site",
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

    page.get_by_role("button", name="Check email settings").click()
    expect(
        page.get_by_text("smtp_host, smtp_port and smtp_from_email are required")
    ).to_be_visible()
    snap("admin_settings_email_check_validation_feedback")


def test_mobile_admin_can_open_nav_and_reach_admin_settings(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="E2E Mobile Admin Nav Site",
        users=[
            SeedUser(
                full_name="Mobile Admin",
                email="mobile-admin@example.com",
                password="MobileAdminPass123!",
                is_admin=True,
            )
        ],
    )

    page, snap = visual_page

    page.set_viewport_size({"width": 390, "height": 844})
    _login(page, "mobile-admin@example.com", "MobileAdminPass123!")
    expect(page).to_have_url(re.compile(".*/dashboard$"))

    menu_button = page.get_by_role("button", name="Toggle navigation menu")
    expect(menu_button).to_be_visible()
    expect(menu_button).to_have_text("Menu")
    menu_button.click()

    expect(menu_button).to_have_text("Close")
    mobile_nav = page.locator("nav ul.md\\:hidden")
    expect(mobile_nav.locator('a[href="/dashboard"]')).to_be_visible()
    expect(mobile_nav.locator('a[href="/profile"]')).to_be_visible()
    expect(mobile_nav.locator('a[href="/users"]')).to_be_visible()
    expect(mobile_nav.locator('a[href="/admin/settings"]')).to_be_visible()
    snap("mobile_admin_nav_open")

    mobile_nav.locator('a[href="/admin/settings"]').click()
    expect(page).to_have_url(re.compile(".*/admin/settings$"))
    expect(page.get_by_text("Admin settings")).to_be_visible()
    expect(menu_button).to_have_text("Menu")
    snap("mobile_admin_settings_from_nav")
