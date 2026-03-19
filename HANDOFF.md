# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work centralized shared auth/setup test defaults so local and CI test environments cannot drift.

## Completed in this session
- Added `backend/tests/test_env.py` as the shared source of truth for test auth/setup defaults (`TEST_AUTH_SECRET_KEY`, `TEST_INITIAL_SETUP_TOKEN`).
- Updated `backend/tests/conftest.py`, `backend/tests/api/test_setup.py`, `backend/tests/e2e/test_setup_e2e.py`, `frontend/tests/conftest.py`, and `frontend/tests/test_setup_initialization_e2e.py` to use those shared constants instead of duplicating hardcoded auth/setup values.
- Removed duplicated `AUTH_SECRET_KEY` and `INITIAL_SETUP_TOKEN` entries from the `backend-quality` and `frontend-e2e` jobs in `.github/workflows/ci.yml`, so CI test jobs now use the same test-harness defaults as local runs instead of maintaining a second copy.
- Re-ran targeted checks with `PYTHONPATH=. .venv/bin/pytest tests/api/test_setup.py tests/e2e/test_setup_e2e.py -q`, `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q`, and YAML validation for `.github/workflows/ci.yml`.
- Re-ran the full backend suite with `PYTHONPATH=. .venv/bin/pytest -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.

## Current status
Shared auth/setup test defaults now live in one helper, and both backend and frontend test harnesses read from it. The full backend suite is green (`140 passed`), and the full frontend verification set is green (`107` Vitest tests, `17` browser tests). CI test jobs no longer carry their own copy of the auth/setup secrets, which closes the drift path that caused the earlier setup-token mismatch.

## Next step
Confirm the next GitHub Actions run stays green with the simplified test-job env config. If any remaining CI noise appears, treat it as a new issue rather than revisiting auth/setup token drift.

## Important files
- AGENTS.md
- HANDOFF.md
- .github/workflows/ci.yml
- backend/tests/test_env.py
- backend/tests/conftest.py
- backend/tests/api/test_setup.py
- backend/tests/e2e/test_setup_e2e.py
- frontend/tests/conftest.py
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The current auth/test hygiene state is: shared auth/setup defaults are defined once in `backend/tests/test_env.py`, backend and frontend test harnesses both import them, and the CI test jobs no longer override those values separately. That removes the earlier three-way drift between backend tests, frontend browser tests, and workflow env config that caused the setup-token mismatch. The Playwright FastAPI fixture in `frontend/tests/conftest.py` still uses `ws="websockets-sansio"` to avoid the old websocket deprecation warnings.

## Last updated
2026-03-19 02:57 UTC
