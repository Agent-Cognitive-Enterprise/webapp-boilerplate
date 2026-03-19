# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work fixed the setup flow at the shared API-client layer after identifying a likely backend-recovery reload race.

## Completed in this session
- Identified a more plausible root cause for the repeated CI-only setup failure: `frontend/src/api/api.ts` would hard-reload the browser on the first successful response after any transient backend/network error, including a successful `POST /setup`, which could wipe out the setup success state before the post-setup redirect flag was recorded.
- Updated `frontend/src/api/api.ts` so backend-recovery hard reloads only happen for safe read methods (`GET`, `HEAD`, `OPTIONS`), while successful mutating requests like `POST /setup` now complete normally without a forced page reload.
- Added regression coverage in `frontend/src/api/api.test.ts` for both sides of that behavior: no hard reload after backend recovery on successful `POST` requests, and preserved hard reload behavior on successful `GET` requests.
- Re-ran focused regression checks for the setup flow with `npx vitest run src/api/api.test.ts src/components/SetupWizard.test.tsx src/App.test.tsx` and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.

## Current status
Frontend browser coverage now includes setup, auth/login/logout, admin locale propagation, authenticated locale switching to RTL, mobile admin navigation, admin email-settings validation feedback, password reset, email verification, admin user management, duplicate registration feedback, invalid verify-email token feedback, and invalid reset-password token feedback. The full local frontend verification set is green, including `17` browser tests and `107` Vitest checks. The setup flow still has the app-level and browser-level redirect safeguards, but the most likely real fix for the GitHub-hosted failure is now in the shared API client: successful `POST /setup` responses are no longer interrupted by the backend-recovery hard reload path.

## Next step
Confirm the next GitHub Actions run is green for both `frontend-e2e` and the upgraded workflow actions. If `frontend-e2e` still fails, inspect the job artifacts/logs for whether setup submission itself is failing before any redirect logic runs.

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
The setup redirect failure repeated with materially unchanged evidence across several redirect-focused iterations, so the next investigation moved down a layer into the shared API client. The likely race is that `frontend/src/api/api.ts` tracked a prior transient backend/network failure by setting `backendDown = true`, then hard-reloaded the entire browser on the next successful response. If that successful response was `POST /setup`, the page could reload `/setup` before the setup success branch persisted the redirect state, leaving the test stuck on `/setup` even though initialization had succeeded. That client path now only hard-reloads after backend recovery for safe read methods. Local focused tests and the full frontend verification suite are green with that fix. The earlier `actions/upload-artifact@v5` warning the user pasted was stale; current workflow files already use `actions/upload-artifact@v6`.

## Last updated
2026-03-19 01:13 UTC
