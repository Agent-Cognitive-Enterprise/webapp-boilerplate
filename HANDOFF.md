# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work hardened the setup redirect again for GitHub-hosted browser timing and finished the last Node 20-based action upgrade.

## Completed in this session
- Confirmed via the GitHub Actions API that CI run `23273853959` on `main` and `head_sha 0809048` still fails in `frontend-e2e`, so the setup redirect issue is real on the current commit and not just stale logs.
- Added a browser-level fallback in `frontend/src/components/SetupWizard.tsx`: after successful initialization, if the page is still on `/setup` on the next tick, the browser now forces `window.location.replace("/login")`.
- Added a regression test in `frontend/src/components/SetupWizard.test.tsx` that stubs `window.location.replace`, advances fake timers, and proves the fallback fires when the path remains `/setup`.
- Re-ran focused regression checks for the setup flow with `npx vitest run src/components/SetupWizard.test.tsx src/App.test.tsx` and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.
- Upgraded deprecated GitHub Actions in `.github/workflows/ci.yml` and `.github/workflows/scorecard.yml` to Node 24-ready majors: `actions/setup-node@v5`, `actions/setup-python@v6`, and `actions/upload-artifact@v6`.

## Current status
Frontend browser coverage now includes setup, auth/login/logout, admin locale propagation, authenticated locale switching to RTL, mobile admin navigation, admin email-settings validation feedback, password reset, email verification, admin user management, duplicate registration feedback, invalid verify-email token feedback, and invalid reset-password token feedback. The full local frontend verification set is green again, including `17` browser tests, and the setup flow now has three layers of protection: the app-level redirect marker in `frontend/src/App.tsx`, effect-driven navigation off `/setup`, and a browser-level fallback in `frontend/src/components/SetupWizard.tsx` if the route still has not changed.

## Next step
Confirm the next GitHub Actions run is green for both `frontend-e2e` and the upgraded workflow actions. If `frontend-e2e` still fails, inspect the job artifacts/logs for whether setup submission itself is failing or whether only the client-side redirect is still being lost.

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
The setup redirect regression repeated with materially unchanged evidence across several iterations. The current state is: `App.tsx` persists the post-setup redirect marker in `sessionStorage` and navigates away from `/setup` from an effect, while `SetupWizard.tsx` now also forces `window.location.replace("/login")` on the next tick if the browser is still sitting on `/setup` after a successful submit. Local focused tests and the full `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q` suite are green with that change, so the next signal needs to come from GitHub Actions rather than another similar local-only redirect tweak. Separately, the earlier `actions/upload-artifact@v5` warning the user pasted was stale; current workflow files already use `actions/upload-artifact@v6`. Keep clearing backend auth `_RATE_BUCKETS` in `frontend/tests/state_helpers.py` during resets to avoid suite-only rate-limit flakes.

## Last updated
2026-03-19 01:00 UTC
