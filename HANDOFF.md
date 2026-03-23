# HANDOFF

## Current objective
Keep the hardened auth stack and new DB configuration path stable. The backend now supports SQLite and PostgreSQL; the next production-readiness work should focus on deployment ergonomics and operational clarity rather than DB backend lock-in.

## Completed in this session
- Switched browser auth from `localStorage` bearer tokens to cookie-backed sessions and made frontend auth state derive from `/users/me/` plus `/auth/refresh`.
- Added CSRF protection for unsafe cookie-authenticated requests and added backend CSP headers with no remaining inline exception.
- Replaced refresh-token IP/User-Agent lockstep with a dedicated HttpOnly session-binding cookie, including legacy refresh-token migration support.
- Added a DB-backed auth rate limiter via `auth_rate_limit_events` plus migration `20260323_02_add_auth_rate_limit_events.py`.
- Replaced the old in-memory auth limiter logic in `backend/api/auth_shared.py` with async SQL-backed tracking and cleanup.
- Added focused regression coverage in `backend/tests/api/test_auth_rate_limit.py`.
- Added shared database URL resolution so the app and Alembic both support SQLite and PostgreSQL from the same environment settings.
- Kept SQLite support for local development and small single-node deployments, and added PostgreSQL support for standard production deployments.
- Added focused resolver tests in `backend/tests/utils/test_db_config.py`.
- Updated `backend/.env.example`, `backend/requirements.txt`, `backend/alembic.ini`, and `README.md` to document the new DB support model truthfully.
- Re-ran full backend verification successfully after the DB configuration change.

## Current status
Browser auth is cookie-backed and no longer depends on `localStorage` bearer tokens. Refresh uses a dedicated session-binding cookie instead of IP/User-Agent enforcement, unsafe cookie-authenticated requests require a trusted `Origin` or `Referer`, backend responses emit a single default CSP, auth throttling is stored in the database rather than a process-local dict, and the backend now supports SQLite plus PostgreSQL through a shared DB URL resolver. Backend verification is green from the current tree: `187` tests passed.

## Next step
Next meaningful step is the production deployment story: add a concrete PostgreSQL-backed deploy path (for example Docker Compose or reverse-proxy + app + Postgres) and document the recommended production topology end to end.

## Important files
- AGENTS.md
- HANDOFF.md
- AUTHENTICATION_FLOW.md
- README.md
- frontend/README.md
- backend/api/auth_shared.py
- backend/api/auth_sessions.py
- backend/auth/cookies.py
- backend/alembic/versions/20260323_01_add_refresh_token_binding_hash.py
- backend/alembic/versions/20260323_02_add_auth_rate_limit_events.py
- backend/alembic/env.py
- backend/alembic.ini
- backend/models/auth_rate_limit_event.py
- backend/security/csrf.py
- backend/security/csp.py
- backend/tests/api/test_csrf.py
- backend/tests/api/test_auth_rate_limit.py
- backend/tests/api/test_security_headers.py
- backend/tests/utils/test_db_config.py
- backend/utils/db.py
- backend/utils/db_config.py
- frontend/src/api/api.ts
- frontend/src/contexts/AuthContext.tsx
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The important behavioral changes are: browser auth no longer survives by writing a JWT into `localStorage`, unsafe cookie-authenticated requests need a trusted `Origin` or `Referer`, backend responses include a single default CSP, refresh depends on a dedicated HttpOnly session-binding cookie rather than IP/User-Agent lockstep, auth rate limiting is DB-backed through `auth_rate_limit_events`, and the backend database path is now resolved from `DATABASE_URL` or a SQLite fallback shared by runtime and Alembic. Header-based bearer auth still exists for non-browser clients and API-style tests. Browser pytest still needs to run serially because `frontend/tests/conftest.py` shares `frontend_e2e.db`.

## Last updated
2026-03-23 01:06 UTC
