# Backend Test Suites

- `tests/utils`, `tests/auth`, `tests/services`: focused unit-level tests.
- `tests/api`: endpoint-focused API/integration tests (single-endpoint behavior, validation, contract checks).
- `tests/e2e`: end-to-end backend flows across multiple endpoints and state transitions.
  Current e2e flows cover:
  - setup guard + initialization lock behavior,
  - auth lifecycle (register/login/refresh/logout),
  - refresh token replay security,
  - password reset lifecycle,
  - email verification lifecycle,
  - setup/admin SMTP connectivity checks,
  - admin settings lifecycle updates,
  - admin user management lifecycle.
- `tests/i18n`: localization utility tests (locale resolution, catalog fallback behavior).

Run backend e2e tests:

```bash
PYTHONPATH=. .venv/bin/pytest tests/e2e -q
```

Run i18n audit:

```bash
PYTHONPATH=. .venv/bin/python scripts/i18n_audit.py
```
