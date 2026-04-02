# Backend Test Suites

## Shared test env defaults

Auth/setup test defaults live in `backend/tests/test_env.py`.

- Use those constants for test auth/setup values instead of hardcoding duplicate secrets or setup tokens in individual tests.
- Do not duplicate `AUTH_SECRET_KEY` or `INITIAL_SETUP_TOKEN` in CI test-job `env` blocks.
- `.github/workflows/ci.yml` is guarded by `backend/scripts/check_ci_test_env.py` to enforce that rule.
- Automated browser-style test runs should set `UI_LABEL_BACKGROUND_TASKS_ENABLED=false` so background UI-label jobs do not create live provider traffic.

- `tests/utils`, `tests/auth`, `tests/services`: focused unit-level tests.
- `tests/api`: endpoint-focused API/integration tests (single-endpoint behavior, validation, contract checks, protected-route probe regressions, cookie-auth session regressions, and live-server runtime smoke checks).
- `tests/e2e`: end-to-end backend flows across multiple endpoints and state transitions. Current e2e flows cover:
  - setup guard + initialization lock behavior,
  - auth lifecycle (register/login/refresh/logout),
  - refresh token replay security,
  - password reset lifecycle,
  - email verification lifecycle,
  - setup/admin SMTP connectivity checks,
  - admin settings lifecycle updates,
  - admin user management lifecycle.
- `tests/scripts`: regression tests for repository helper scripts and deployment examples.
- `tests/ai`: focused coverage for the AI translation agent and OpenAI client wrapper behavior.
- `tests/i18n`: localization utility tests (locale resolution, catalog fallback behavior).

Run backend e2e tests:

```bash
PYTHONPATH=. .venv/bin/pytest tests/e2e -q
```

Run focused protected-route and cookie-auth runtime smoke coverage:

```bash
PYTHONPATH=. .venv/bin/pytest \
  tests/api/test_protected_route_probes.py \
  tests/api/test_protected_route_runtime_smoke.py \
  tests/api/test_auth_refresh.py \
  tests/api/test_auth_refresh_failure_cookies.py \
  tests/api/test_auth_logout_api.py -q
```

That focused slice now covers:
- protected-route `401`/`403`/`405` ordering for `/admin/settings`, `/admin/settings/email/check`, `/users`, `/users/{id}`, `/users/me/`, and `/user-settings`,
- trusted vs untrusted `Origin` handling for cookie-authenticated writes on `/admin/settings`, `/user-settings`, `/auth/refresh`, and `/auth/logout`,
- refresh missing/invalid/expired/replayed/tampered/inactive/unverified failure branches with delete-cookie assertions,
- legacy refresh-token migration when `client_binding_hash` is absent, plus rotation/reuse invalidation over live HTTP.

Run the CI test-env drift guard locally:

```bash
.venv/bin/python scripts/check_ci_test_env.py
```

Run i18n audit:

```bash
PYTHONPATH=. .venv/bin/python scripts/i18n_audit.py
```
