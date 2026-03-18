# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest non-app issue was the Scorecard workflow failing Sigstore signing because it lacked GitHub OIDC permissions.

## Completed in this session
- Fixed the setup post-submit redirect race by removing the duplicate child-side navigation from `frontend/src/components/SetupWizard.tsx` and letting `frontend/src/App.tsx` remain the single redirect source after successful initialization.
- Re-ran focused regression checks for the setup flow with `npx vitest run src/App.test.tsx src/components/SetupWizard.test.tsx` and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.
- Fixed the GitHub Scorecard workflow permissions in `.github/workflows/scorecard.yml` by moving write permissions to the job and adding `id-token: write`, so Sigstore can use GitHub Actions OIDC instead of falling back to an interactive device flow.

## Current status
Frontend browser coverage now includes setup, auth/login/logout, admin locale propagation, password reset, email verification, admin user management, duplicate registration feedback, invalid verify-email token feedback, and invalid reset-password token feedback. The setup browser flow is back to reliably landing on `/login` immediately after initialization, the full frontend verification set is green, and the Scorecard workflow now has the OIDC permissions needed for non-interactive Sigstore signing.

## Next step
Confirm the Scorecard workflow passes on the next GitHub Actions run, then return to the remaining low-coverage UI edge cases such as admin settings failure feedback or mobile-specific admin interactions.

## Important files
- AGENTS.md
- HANDOFF.md
- .github/workflows/scorecard.yml
- frontend/src/App.tsx
- frontend/src/App.test.tsx
- frontend/src/components/SetupWizard.tsx
- frontend/src/components/SetupWizard.test.tsx
- frontend/tests/test_auth_and_admin_e2e.py
- frontend/tests/test_setup_initialization_e2e.py
- frontend/tests/test_password_reset_and_verification_e2e.py

## Notes for next session
Keep setup redirect ownership in one place. The regression resurfaced while `SetupWizard.tsx` and `App.tsx` were both trying to navigate after setup; removing the child `navigate("/login")` restored deterministic browser behavior. Separately, the Scorecard failure was a workflow-permissions issue, not an app issue: Sigstore was falling back to device flow and expiring because the job lacked `id-token: write`. The browser suite still leans on deterministic monkeypatches for reset/verification token generation and email sending, plus stable DOM hooks like `name`, `aria-label`, row filters, and direct form-button locators where `UiLabel`-driven text proved unreliable for Playwright.

## Last updated
2026-03-18 23:26 UTC
