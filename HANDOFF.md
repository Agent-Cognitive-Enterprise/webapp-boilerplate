# HANDOFF

## Current objective
Continue improving project structure and workflow discipline, with the next focus on reducing auth/session coupling and tightening frontend security behavior.

## Completed in this session
- Added repository rules to `AGENTS.md` for code shape, test performance, delivery flow, and session handoff discipline.
- Removed runtime schema mutation from backend startup and made Alembic the explicit schema migration path.
- Added `make backend-migrate`, updated backend dev/test commands to use the project venv, and documented the migration-first backend workflow.
- Added a backend regression test to verify startup no longer depends on schema bootstrap side effects.
- Refactored `frontend/src/App.tsx` into smaller units by extracting setup bootstrap logic, backend health polling, and the initialized app shell.
- Kept the extracted frontend files under the new soft size limit and preserved existing route/setup behavior.

## Current status
Backend startup no longer runs `create_all()` or ad hoc `ALTER TABLE` logic. `frontend/src/App.tsx` is now a small coordinator, with responsibilities split into `InitializedAppShell`, `useSetupBootstrap`, and `useBackendHealth`. Frontend lint and the full frontend test suite passed after the refactor.

## Next step
Refactor frontend auth/session handling in `frontend/src/contexts/AuthContext.tsx` and related API usage so logout is resilient to backend failures and token state management is less coupled to `localStorage`.

## Important files
- AGENTS.md
- HANDOFF.md
- backend/utils/db.py
- backend/api/lifespan.py
- backend/tests/api/test_lifespan.py
- Makefile
- README.md
- frontend/src/App.tsx
- frontend/src/components/InitializedAppShell.tsx
- frontend/src/hooks/useSetupBootstrap.ts
- frontend/src/hooks/useBackendHealth.ts
- frontend/src/contexts/AuthContext.tsx
- frontend/src/api/api.ts

## Notes for next session
Use `frontend/src/App.test.tsx` and the auth-related component tests as the safety net for the next refactor. The `useBackendHealth` hook now honors `VITE_BACKEND_POLL_INTERVAL`, which aligns code with existing docs.

## Last updated
2026-03-18 10:10 UTC
