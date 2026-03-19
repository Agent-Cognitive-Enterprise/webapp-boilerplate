import hashlib
import re

import api.auth as auth_api
import api.auth_account_recovery as auth_recovery_api
from playwright.sync_api import expect

from frontend.tests.conftest import FAST_API_BASE_URL, FRONTEND_BASE_URL
from frontend.tests.state_helpers import (
    SeedEmailSettings,
    SeedUser,
    reset_uninitialized_state,
    seed_initialized_state,
)


def _login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND_BASE_URL}/login")
    page.get_by_label("email").fill(email)
    page.get_by_label("password").fill(password)
    page.locator("button[type='submit']").click()


def test_forgot_password_and_reset_journey(visual_page, monkeypatch):
    reset_uninitialized_state()
    seed_initialized_state(
        users=[
            SeedUser(
                full_name="Reset User",
                email="password-reset@example.com",
                password="InitialPass123!",
            )
        ]
    )

    plain_reset_token = "browser-reset-token"
    monkeypatch.setattr(
        auth_recovery_api,
        "generate_reset_token",
        lambda: (
            plain_reset_token,
            hashlib.sha256(plain_reset_token.encode()).hexdigest(),
        ),
    )

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/forgot-password")
    expect(page).to_have_url(re.compile(".*/forgot-password$"))

    page.locator('input[name="email"]').fill("password-reset@example.com")
    snap("forgot_password_form_filled")
    page.locator('form button[type="submit"]').click()

    expect(page.locator('a.ace-primary-btn[href="/login"]')).to_be_visible()
    snap("forgot_password_success")

    page.goto(f"{FRONTEND_BASE_URL}/reset-password?token={plain_reset_token}")
    page.locator('input[name="password"]').fill("UpdatedPass123!")
    page.locator('input[name="confirmPassword"]').fill("UpdatedPass123!")
    snap("reset_password_form_filled")
    page.locator('form button[type="submit"]').click()

    expect(page).to_have_url(re.compile(".*/login\\?reset=success$"))
    snap("reset_password_redirect_to_login")

    page.get_by_label("email").fill("password-reset@example.com")
    page.get_by_label("password").fill("InitialPass123!")
    page.locator("button[type='submit']").click()
    expect(page.get_by_text("Invalid email or password")).to_be_visible()

    page.get_by_label("password").fill("UpdatedPass123!")
    page.locator("button[type='submit']").click()
    expect(page).to_have_url(re.compile(".*/dashboard$"))
    expect(page.get_by_text("password-reset@example.com")).to_be_visible()
    snap("dashboard_after_password_reset")


def test_email_verification_browser_journey(visual_page, monkeypatch):
    reset_uninitialized_state()
    seed_initialized_state(
        site_name="Verification Journey Site",
        email_settings=SeedEmailSettings(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_from_email="noreply@example.com",
            smtp_username="smtp-user",
            smtp_password="smtp-pass",
            auth_frontend_base_url=FRONTEND_BASE_URL,
            auth_backend_base_url=FAST_API_BASE_URL,
        ),
    )

    plain_verification_token = "browser-verification-token"
    monkeypatch.setattr(
        auth_api,
        "generate_email_verification_token",
        lambda: (
            plain_verification_token,
            hashlib.sha256(plain_verification_token.encode()).hexdigest(),
        ),
    )
    monkeypatch.setattr(auth_api, "send_email", lambda **_: None)

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/register")
    page.locator('input[name="full_name"]').fill("Needs Verification")
    page.locator('input[name="email"]').fill("verify-browser@example.com")
    page.locator('input[name="password"]').fill("NeedsVerify123!")
    snap("register_form_filled_for_verification")
    page.get_by_role("button", name="Register").click()

    expect(page).to_have_url(re.compile(".*/login$"))
    snap("login_after_registration_pending_verification")

    page.get_by_label("email").fill("verify-browser@example.com")
    page.get_by_label("password").fill("NeedsVerify123!")
    page.locator("button[type='submit']").click()
    expect(
        page.get_by_text("Email verification required. Please check your inbox.")
    ).to_be_visible()
    snap("login_blocked_until_email_verified")

    page.goto(f"{FAST_API_BASE_URL}/auth/verify-email?token={plain_verification_token}")
    expect(page).to_have_url(re.compile(".*/login$"))

    page.get_by_label("email").fill("verify-browser@example.com")
    page.get_by_label("password").fill("NeedsVerify123!")
    page.locator("button[type='submit']").click()
    expect(page).to_have_url(re.compile(".*/dashboard$"))
    expect(page.get_by_text("verify-browser@example.com")).to_be_visible()
    snap("dashboard_after_email_verification")


def test_duplicate_registration_shows_browser_error_feedback(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(
        users=[
            SeedUser(
                full_name="Existing User",
                email="existing@example.com",
                password="ExistingPass123!",
            )
        ]
    )

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/register")
    page.locator('input[name="full_name"]').fill("Duplicate User")
    page.locator('input[name="email"]').fill("existing@example.com")
    page.locator('input[name="password"]').fill("AnotherPass123!")
    snap("duplicate_registration_form_filled")
    page.locator("form button[type='submit']").click()

    expect(page).to_have_url(re.compile(".*/register$"))
    expect(page.get_by_text("Email already registered.")).to_be_visible()
    snap("duplicate_registration_error")


def test_invalid_verify_email_token_shows_browser_feedback_page(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(site_name="Invalid Verify Token Site")

    page, snap = visual_page

    page.goto(f"{FAST_API_BASE_URL}/auth/verify-email?token=invalid-token")
    expect(page.get_by_text("Invalid or already used verification token")).to_be_visible()
    expect(page.get_by_role("link", name="Go now")).to_be_visible()
    snap("invalid_verify_token_feedback")


def test_invalid_reset_password_token_shows_browser_error_feedback(visual_page):
    reset_uninitialized_state()
    seed_initialized_state(site_name="Invalid Reset Token Site")

    page, snap = visual_page

    page.goto(f"{FRONTEND_BASE_URL}/reset-password?token=invalid-token")
    page.locator('input[name="password"]').fill("UpdatedPass123!")
    page.locator('input[name="confirmPassword"]').fill("UpdatedPass123!")
    page.locator("form button[type='submit']").click()

    expect(page.get_by_text("Invalid or already used reset token")).to_be_visible()
    snap("invalid_reset_token_error")
