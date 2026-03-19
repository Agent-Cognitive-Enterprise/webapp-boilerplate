# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work hardened the setup redirect against CI-only rerender timing and updated the remaining Node 20-based GitHub Actions.

## Completed in this session
- Fixed the setup post-submit redirect race by removing the duplicate child-side navigation from `frontend/src/components/SetupWizard.tsx` and letting `frontend/src/App.tsx` remain the single redirect source after successful initialization.
- Re-ran focused regression checks for the setup flow with `npx vitest run src/App.test.tsx src/components/SetupWizard.test.tsx` and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.
- Fixed the GitHub Scorecard workflow permissions in `.github/workflows/scorecard.yml` by moving write permissions to the job and adding `id-token: write`, so Sigstore can use GitHub Actions OIDC instead of falling back to an interactive device flow.
- Added admin email-settings failure feedback coverage in `frontend/src/components/AdminSettings.test.tsx` and `frontend/tests/test_auth_and_admin_e2e.py`.
- Stabilized the admin-settings setup browser test by removing its dependency on the rate-limited `/auth/token` endpoint and generating a local access token in `frontend/tests/state_helpers.py`.
- Added authenticated locale-switching coverage in `frontend/tests/test_auth_and_admin_e2e.py` for changing the profile page locale to Arabic and asserting RTL document state after reload.
- Fixed browser-suite rate-limit leakage by clearing backend auth `_RATE_BUCKETS` in `frontend/tests/state_helpers.py` during test resets.
- Added mobile admin-navigation coverage in `frontend/tests/test_auth_and_admin_e2e.py` by opening the authenticated mobile menu, asserting admin routes are present, and reaching `/admin/settings` through the menu itself.
- Hardened the setup redirect in `frontend/src/App.tsx` by persisting the post-setup redirect marker in `sessionStorage`, so CI/browser rerenders still land on `/login` after initialization.
- Updated remaining deprecated GitHub Actions in `.github/workflows/ci.yml` and `.github/workflows/scorecard.yml`: `actions/setup-node@v5`, `actions/setup-python@v6`, and `actions/upload-artifact@v5`.

## Current status
Frontend browser coverage now includes setup, auth/login/logout, admin locale propagation, authenticated locale switching to RTL, mobile admin navigation, admin email-settings validation feedback, password reset, email verification, admin user management, duplicate registration feedback, invalid verify-email token feedback, and invalid reset-password token feedback. The setup browser flow is back to reliably landing on `/login` immediately after initialization even under CI-style rerenders, the full frontend verification set is green, and the remaining deprecated Node 20-based workflow actions have been upgraded.

## Next step
Confirm the next GitHub Actions run is green for both `frontend-e2e` and the upgraded workflow actions, then decide whether any worthwhile browser gaps remain or shift effort to backend/CI cleanup.

## Important files
- AGENTS.md
- HANDOFF.md
- .github/workflows/ci.yml
- .github/workflows/scorecard.yml
- frontend/src/App.tsx
- frontend/src/App.test.tsx
- frontend/src/components/AdminSettings.test.tsx
- frontend/src/components/SetupWizard.tsx
- frontend/src/components/SetupWizard.test.tsx
- frontend/tests/test_auth_and_admin_e2e.py
- frontend/tests/state_helpers.py
- frontend/tests/test_setup_initialization_e2e.py
- frontend/tests/test_password_reset_and_verification_e2e.py

## Notes for next session
Keep setup redirect ownership in one place. The regression resurfaced while `SetupWizard.tsx` and `App.tsx` were both trying to navigate after setup; removing the child `navigate("/login")` helped, but CI still needed the redirect marker to survive rerenders, so `App.tsx` now persists that one-shot state in `sessionStorage`. Separately, the Scorecard failure was a workflow-permissions issue, not an app issue: Sigstore was falling back to device flow and expiring because the job lacked `id-token: write`. The admin-settings browser coverage now includes the deterministic email-settings validation error path, authenticated profile locale switching is covered for RTL behavior, and the mobile admin menu path is covered through route-based `href` locators. For browser-test stability, keep clearing backend auth `_RATE_BUCKETS` in `reset_uninitialized_state()`; without that, `/auth/token` rate limiting leaks across tests and causes suite-only failures. The browser suite still leans on deterministic monkeypatches for reset/verification token generation and email sending, plus stable DOM hooks like `name`, `aria-label`, row filters, and direct form-button locators where `UiLabel`-driven text proved unreliable for Playwright.

## Last updated
2026-03-19 00:09 UTC
