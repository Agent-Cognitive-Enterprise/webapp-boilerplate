# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work added an explicit CI guard against reintroducing test-job auth/setup env drift.

## Completed in this session
- Added `backend/scripts/check_ci_test_env.py`, a checked-in CI guard that fails if `.github/workflows/ci.yml` reintroduces `AUTH_SECRET_KEY` or `INITIAL_SETUP_TOKEN` in the `backend-quality` or `frontend-e2e` job `env` blocks instead of using the shared test-harness defaults.
- Added focused regression coverage in `backend/tests/scripts/test_check_ci_test_env.py` for both valid and invalid workflow shapes, plus a test that exercises the current workflow file through the script entrypoint.
- Wired the guard into `.github/workflows/ci.yml` as the `Check CI test env drift` step in `backend-quality`.
- Re-ran targeted checks with `PYTHONPATH=. .venv/bin/pytest tests/scripts/test_check_ci_test_env.py -q`, `python scripts/check_ci_test_env.py`, and YAML validation for `.github/workflows/ci.yml`.
- Re-ran the full backend suite with `PYTHONPATH=. .venv/bin/pytest -q`.
- Re-ran the full frontend verification path again: `npm test`, `npm run lint`, `npm run build`, and `PYTHONPATH=..:. .venv/bin/pytest ../frontend/tests -q`.

## Current status
Shared auth/setup test defaults live in one helper, and there is now an explicit CI guard preventing `backend-quality` or `frontend-e2e` from redefining those auth/setup secrets in the workflow. The full backend suite is green (`143 passed`), and the full frontend verification set is green (`107` Vitest tests, `17` browser tests).

## Next step
Confirm the next GitHub Actions run stays green with the new CI drift guard in place. If any remaining CI noise appears, treat it as a new issue rather than revisiting auth/setup token drift.

## Important files
- AGENTS.md
- HANDOFF.md
- .github/workflows/ci.yml
- backend/scripts/check_ci_test_env.py
- backend/tests/scripts/test_check_ci_test_env.py
- backend/tests/test_env.py
- backend/tests/conftest.py
- backend/tests/api/test_setup.py
- backend/tests/e2e/test_setup_e2e.py
- frontend/tests/conftest.py
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The current auth/test hygiene state is: shared auth/setup defaults are defined once in `backend/tests/test_env.py`, backend and frontend test harnesses both import them, the CI test jobs no longer override those values separately, and `backend/scripts/check_ci_test_env.py` now enforces that rule in CI. That closes the earlier three-way drift between backend tests, frontend browser tests, and workflow env config that caused the setup-token mismatch. The Playwright FastAPI fixture in `frontend/tests/conftest.py` still uses `ws="websockets-sansio"` to avoid the old websocket deprecation warnings.

## Last updated
2026-03-19 03:07 UTC
