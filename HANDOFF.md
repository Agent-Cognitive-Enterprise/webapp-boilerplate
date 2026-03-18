# HANDOFF

## Current objective
Continue improving project structure and workflow discipline, with the next focus on further decoupling frontend auth/session behavior and reducing remaining coupling around refresh/logout flows.

## Completed in this session
- Added repository rules to `AGENTS.md` for code shape, test performance, delivery flow, and session handoff discipline.
- Removed runtime schema mutation from backend startup and made Alembic the explicit schema migration path.
- Added `make backend-migrate`, updated backend dev/test commands to use the project venv, and documented the migration-first backend workflow.
- Added a backend regression test to verify startup no longer depends on schema bootstrap side effects.
- Refactored `frontend/src/App.tsx` into smaller units by extracting setup bootstrap logic, backend health polling, and the initialized app shell.
- Kept the extracted frontend files under the new soft size limit and preserved existing route/setup behavior.
- Centralized frontend access-token persistence in `frontend/src/auth/tokenStore.ts`.
- Refactored `AuthContext` to clear client auth state in `finally` during logout and removed local-storage side effects from `api/auth.ts`.
- Added `frontend/src/contexts/AuthContext.test.tsx` to cover login persistence and logout resilience when backend logout fails.

## Current status
Backend startup no longer runs `create_all()` or ad hoc `ALTER TABLE` logic. `frontend/src/App.tsx` is now a small coordinator, and frontend token persistence now goes through a shared token store used by both `AuthContext` and the Axios refresh interceptor. Frontend lint and the full frontend test suite passed after the refactors.

## Next step
Refactor `frontend/src/api/api.ts` refresh-failure handling so session invalidation and redirect behavior are coordinated through a shared auth/session mechanism rather than direct `window.location.href` mutation inside the Axios interceptor.

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
- frontend/src/api/auth.ts
- frontend/src/auth/tokenStore.ts
- frontend/src/contexts/AuthContext.test.tsx

## Notes for next session
Use `frontend/src/contexts/AuthContext.test.tsx`, `frontend/src/App.test.tsx`, and the existing auth-related component tests as the safety net for the next refactor. The remaining auth coupling is in the interceptor path: refresh failure still clears the token and hard-redirects directly from `api.ts`.

## Last updated
2026-03-18 10:15 UTC
