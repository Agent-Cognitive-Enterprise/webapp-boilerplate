# HANDOFF

## Current objective
Keep CI stable while continuing cross-stack browser coverage improvements. The latest completed work documented the shared test-env contract so future contributors can follow the CI guard instead of fighting it.

## Completed in this session
- Documented the shared auth/setup test-env contract in `backend/tests/README.md`, including the rule that `backend/tests/test_env.py` is the source of truth and that CI test-job `env` blocks must not duplicate `AUTH_SECRET_KEY` or `INITIAL_SETUP_TOKEN`.
- Added the local `python scripts/check_ci_test_env.py` command to the backend command list in `README.md` and documented the same no-duplication rule there for contributors working from the main project docs.
- Re-ran the CI drift guard locally with `python scripts/check_ci_test_env.py` after the documentation update.

## Current status
Shared auth/setup test defaults live in one helper, there is an explicit CI guard preventing `backend-quality` or `frontend-e2e` from redefining those auth/setup secrets in the workflow, and that contract is now documented in both the main README and the backend test README. The last full verification state remains green: backend `143 passed`, frontend `107` Vitest tests, browser `17 passed`.

## Next step
Confirm the next GitHub Actions run stays green with the documented CI drift guard in place. If any remaining CI noise appears, treat it as a new issue rather than revisiting auth/setup token drift.

## Important files
- AGENTS.md
- HANDOFF.md
- README.md
- .github/workflows/ci.yml
- backend/scripts/check_ci_test_env.py
- backend/tests/README.md
- backend/tests/scripts/test_check_ci_test_env.py
- backend/tests/test_env.py
- backend/tests/conftest.py
- backend/tests/api/test_setup.py
- backend/tests/e2e/test_setup_e2e.py
- frontend/tests/conftest.py
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The current auth/test hygiene state is: shared auth/setup defaults are defined once in `backend/tests/test_env.py`, backend and frontend test harnesses both import them, the CI test jobs no longer override those values separately, and `backend/scripts/check_ci_test_env.py` enforces that rule in CI. That contract is now also documented in `README.md` and `backend/tests/README.md`, so future contributors have both the policy and the enforcement path in view. The Playwright FastAPI fixture in `frontend/tests/conftest.py` still uses `ws="websockets-sansio"` to avoid the old websocket deprecation warnings.

## Last updated
2026-03-19 03:17 UTC
