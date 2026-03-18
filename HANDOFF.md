# HANDOFF

## Current objective
Continue improving project structure and workflow discipline, with the next focus on breaking up frontend gravity wells starting with `frontend/src/App.tsx`.

## Completed in this session
- Added repository rules to `AGENTS.md` for code shape, test performance, delivery flow, and session handoff discipline.
- Removed runtime schema mutation from backend startup and made Alembic the explicit schema migration path.
- Added `make backend-migrate`, updated backend dev/test commands to use the project venv, and documented the migration-first backend workflow.
- Added a backend regression test to verify startup no longer depends on schema bootstrap side effects.

## Current status
Backend startup no longer runs `create_all()` or ad hoc `ALTER TABLE` logic. Targeted backend tests and frontend lint passed after the refactor. The next recommended refactor is frontend-side: `frontend/src/App.tsx` is still a large multi-responsibility file.

## Next step
Refactor `frontend/src/App.tsx` by extracting setup/bootstrap logic, backend health polling, and layout/routing responsibilities into focused hooks or components while preserving behavior and test coverage.

## Important files
- AGENTS.md
- HANDOFF.md
- backend/utils/db.py
- backend/api/lifespan.py
- backend/tests/api/test_lifespan.py
- Makefile
- README.md
- frontend/src/App.tsx

## Notes for next session
Use the existing frontend test suite as the safety net, especially `frontend/src/App.test.tsx`. Keep the refactor scoped; the goal is decomposition, not feature changes.

## Last updated
2026-03-18 10:05 UTC
