# HANDOFF

## Current objective
Keep direct backend startup safe and predictable for SQLite while preserving explicit migration control for import-based and production deployment paths.

## Completed in this session
- Added `backend/services/startup_migrations.py` to decide and run direct-start Alembic preflight for `python main.py` only.
- Wired `backend/main.py` to call the preflight before `uvicorn.run(...)` in the direct entrypoint.
- Normalized SQLite direct-run targets to absolute paths before preflight so Alembic and runtime point at the same DB file.
- Updated `backend/api/health.py` so schema-missing or schema-drift errors return `503` with a clear `alembic upgrade head` hint instead of propagating an ASGI traceback.
- Added regression coverage for startup-migration policy, direct-entrypoint ordering, `/health` degraded behavior, and real-process migrated/unmigrated SQLite smoke cases.
- Updated `backend/.env.example`, `README.md`, and `DEPLOYMENT.md` to document `AUTO_MIGRATE_ON_START`, direct-run behavior, and the `/health` degradation contract.
- Ran full backend verification successfully with `make verify-backend` (`204 passed`, Ruff clean, mypy clean).
- Diagnosed the frontend "Backend is offline" overlay as a local CORS mismatch: `frontend/.env` points at `http://192.168.1.160:8000`, while `backend/.env` only allowed `http://localhost:5173`. Updated local `backend/.env` to allow both frontend origins; backend restart still required to apply it.
- Updated the first-run setup form so `Initial setup token` and `Site name` each occupy their own row in the main form grid.
- Restored the first-run setup beach background by wrapping the setup flow in a dedicated setup shell and switched the setup card to a more translucent frosted-glass treatment.
- Moved `Use STARTTLS` and `Check email settings` into the same control row, with the toggle on the left and the button aligned on the right.
- Reworked the setup shell to use a dedicated centering wrapper with auto vertical margins instead of the shared page padding, so the frosted-glass card centers when space allows and falls back to scroll-safe mobile positioning when the form is taller than the viewport.
- Tightened setup-form mobile spacing and title sizing so more of the first-run form fits on phone screens without losing readability.
- Removed the empty feedback wrapper under `Check email settings` so the setup form no longer leaves dead space below that control when no status message is present.
- Added the repository rule in `AGENTS.md` that frontend visual/layout work must include before-and-after screenshots.
- Added frontend regression coverage for the setup layout/shell updates and re-ran frontend verification successfully with `npm run lint` and `npm test` (`39` files, `143` tests passed).

## Current status
Direct `python main.py` runs now preflight migrations when `APP_ENV` is `development`/`dev`, when `AUTO_MIGRATE_ON_START=true`, or when `AUTO_MIGRATE_ON_START=auto` and the SQLite DB file is missing. Production-like direct runs skip auto-migration by default unless that missing-file SQLite exception or the explicit override applies. Import-based paths such as `uvicorn main:app` still do not auto-migrate. If runtime reaches `/health` with a missing or mismatched schema, the endpoint now returns `503` plus a migration hint and no traceback. Local frontend/backend CORS is configured to support both `localhost` and the current LAN dev origin. The first-run setup flow now uses the beach background, a translucent frosted-glass card, full-row setup token/site name fields, a shared STARTTLS/email-check control row, no empty feedback gap below that control, and a mobile-safe centering wrapper instead of the shared top-heavy page padding. Verification state is green at `204` backend tests passed and `143` frontend tests passed.

## Next step
Next meaningful step is to extend the same schema-unavailable handling to other startup-safe or pre-setup paths so an empty or drifted database never leaks raw SQL errors outside `/health`.

## Important files
- AGENTS.md
- HANDOFF.md
- README.md
- DEPLOYMENT.md
- backend/.env.example
- backend/main.py
- backend/api/health.py
- backend/services/startup_migrations.py
- backend/tests/api/test_health.py
- backend/tests/api/test_health_runtime_smoke.py
- backend/tests/services/test_startup_migrations.py
- backend/tests/test_main_entrypoint.py
- frontend/src/components/setupWizard/SetupWizardForm.tsx
- frontend/src/components/setupWizard/SetupWizardShell.tsx
- frontend/src/components/SetupWizard.tsx
- frontend/src/components/SetupWizard.test.tsx

## Notes for next session
The new startup-migration logic is intentionally scoped to the direct `python main.py` path. Do not move it into `api.lifespan` or generic app import code unless product requirements change. The real-process smoke tests use `uvicorn main:app` specifically to verify that import-based runtime paths still skip auto-migration while `/health` degrades cleanly. If future work touches startup or health behavior, keep the SQLite absolute-path normalization intact so relative `SQLITE_DB_PATH` values behave the same when `main.py` is launched from outside `backend/`.
For the current local dev environment, the frontend is configured for the LAN origin `http://192.168.1.160:5173`, so backend CORS must include that exact origin alongside `http://localhost:5173`.
Frontend screenshot review for the latest setup-shell pass used temporary local captures only and did not leave preview scaffolding in the repo. The latest gap-fix before/after images are `/tmp/setup-gap-before-check-row.png` and `/tmp/setup-gap-after-check-row.png`. The broader mobile centering before/after images from the prior pass are `/tmp/setup-preview-before-mobile.png` and `/tmp/setup-preview-after-mobile.png`.

## Last updated
2026-03-25 05:52 UTC
