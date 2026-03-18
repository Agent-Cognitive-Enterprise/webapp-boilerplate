# HANDOFF

## Current objective
Continue improving project structure and workflow discipline, with the next focus on reducing remaining auth/session coupling and tightening frontend test/runtime ergonomics.

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
- Added a shared session invalidation mechanism in `frontend/src/auth/sessionEvents.ts`.
- Refactored the Axios interceptor and keep-alive hook to use shared session invalidation instead of direct `window.location.href` mutation or forced logout requests after refresh failure.
- Added `frontend/src/api/api.test.ts` and expanded `AuthContext` tests to cover the shared session invalidation flow.

## Current status
Backend startup no longer runs `create_all()` or ad hoc `ALTER TABLE` logic. `frontend/src/App.tsx` is now a small coordinator, frontend token persistence goes through a shared token store, and session invalidation is coordinated through shared auth events rather than hard redirects inside the interceptor. `AGENTS.md` now requires the full backend suite for meaningful backend changes, the full frontend suite for meaningful frontend changes, and both suites for cross-stack changes before marking work complete.

## Next step
Add backend quality gates to CI and local workflow by wiring `ruff` and `mypy` into the backend verification path and documenting the fast/default backend checks.

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
- frontend/src/auth/sessionEvents.ts
- frontend/src/contexts/AuthContext.test.tsx
- frontend/src/api/api.test.ts

## Notes for next session
Use the frontend auth/API tests as the safety net if auth/session work continues. The highest-value repo-level gap now is backend verification drift: `ruff` and `mypy` are installed in backend dev requirements but are not part of CI or the root Make targets. Also follow the new verification default: full affected-stack suites are required before closing a meaningful task.

## Last updated
2026-03-18 10:21 UTC
