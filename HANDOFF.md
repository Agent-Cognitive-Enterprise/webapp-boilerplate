# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work identified the actual CI setup failure as a token mismatch between workflow env and the Playwright test.

## Completed in this session
- Identified the actual GitHub failure from new evidence: `frontend-e2e` sets `INITIAL_SETUP_TOKEN=ci-test-setup-token` in `.github/workflows/ci.yml`, while `frontend/tests/test_setup_initialization_e2e.py` was still hardcoding `test-initial-setup-token`, so the browser setup submit was using the wrong token and correctly getting `{"detail":"Invalid setup token"}`.
- Updated `frontend/tests/test_setup_initialization_e2e.py` to read `SETUP_TOKEN` from `os.environ["INITIAL_SETUP_TOKEN"]` with the existing local fallback, so the browser test always matches the backend token configured for that environment.
- Re-ran the setup browser file with a CI-style override using `INITIAL_SETUP_TOKEN=ci-test-setup-token PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`.
- Re-ran the full frontend verification path again, including the full browser suite under the same CI-style token override: `npm test`, `npm run lint`, `npm run build`, and `INITIAL_SETUP_TOKEN=ci-test-setup-token PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.

## Current status
Frontend browser coverage now includes setup, auth/login/logout, admin locale propagation, authenticated locale switching to RTL, mobile admin navigation, admin email-settings validation feedback, password reset, email verification, admin user management, duplicate registration feedback, invalid verify-email token feedback, and invalid reset-password token feedback. The full local frontend verification set is green, including `17` browser tests and `107` Vitest checks. The actual CI setup failure is now understood and fixed: the browser setup tests were submitting a different token than the backend expected under GitHub Actions.

## Next step
Confirm the next GitHub Actions run is green for `frontend-e2e`. If anything still fails there, treat it as a new issue rather than continuing the old setup-redirect investigation.

## Important files
- AGENTS.md
- HANDOFF.md
- frontend/src/App.tsx
- frontend/src/App.test.tsx
- frontend/src/api/api.ts
- frontend/src/api/api.test.ts
- frontend/src/components/SetupWizard.tsx
- frontend/src/components/SetupWizard.test.tsx
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The earlier setup-redirect debugging loop was overtaken by stronger evidence: the failing GitHub log now showed `{"detail":"Invalid setup token"}` from `POST /setup`. That exposed the real issue. In `.github/workflows/ci.yml`, the `frontend-e2e` job exports `INITIAL_SETUP_TOKEN=ci-test-setup-token`, but `frontend/tests/test_setup_initialization_e2e.py` had been hardcoding `test-initial-setup-token`. The backend was correct to reject the browser submission. The browser setup test now reads the token from `os.environ`, so it matches the backend token in both local and CI environments. The previous shared-client hardening in `frontend/src/api/api.ts` and the browser-test resilience changes in `frontend/tests/test_setup_initialization_e2e.py` remain in place, but the root cause for the current GitHub failure was the token mismatch, not the redirect path.

## Last updated
2026-03-19 01:34 UTC
