# HANDOFF

## Current objective
Keep the hardened auth stack stable and move to the next production-readiness gap. The shared auth rate limiter is now DB-backed; the biggest remaining infrastructure limitation is still the SQLite-only backend story.

## Completed in this session
- Switched browser auth from `localStorage` bearer tokens to cookie-backed sessions and made frontend auth state derive from `/users/me/` plus `/auth/refresh`.
- Added CSRF protection for unsafe cookie-authenticated requests and added backend CSP headers with no remaining inline exception.
- Replaced refresh-token IP/User-Agent lockstep with a dedicated HttpOnly session-binding cookie, including legacy refresh-token migration support.
- Added a DB-backed auth rate limiter via `auth_rate_limit_events` plus migration `20260323_02_add_auth_rate_limit_events.py`.
- Replaced the old in-memory auth limiter logic in `backend/api/auth_shared.py` with async SQL-backed tracking and cleanup.
- Added focused regression coverage in `backend/tests/api/test_auth_rate_limit.py`.
- Re-ran full backend verification successfully after the rate-limit change.

## Current status
Browser auth is cookie-backed and no longer depends on `localStorage` bearer tokens. Refresh uses a dedicated session-binding cookie instead of IP/User-Agent enforcement, unsafe cookie-authenticated requests require a trusted `Origin` or `Referer`, backend responses emit a single default CSP, and auth throttling is now stored in the database rather than a process-local dict. Backend verification is green from the current tree: `182` tests passed.

## Next step
Next meaningful step is the production data/deployment story: add a real production database path beyond SQLite, or explicitly narrow the repo’s positioning so it stops implying multi-node readiness it does not yet provide.

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
- backend/models/auth_rate_limit_event.py
- backend/security/csrf.py
- backend/security/csp.py
- backend/tests/api/test_csrf.py
- backend/tests/api/test_auth_rate_limit.py
- backend/tests/api/test_security_headers.py
- frontend/src/api/api.ts
- frontend/src/contexts/AuthContext.tsx
- frontend/tests/test_setup_initialization_e2e.py

## Notes for next session
The important behavioral changes are: browser auth no longer survives by writing a JWT into `localStorage`, unsafe cookie-authenticated requests need a trusted `Origin` or `Referer`, backend responses include a single default CSP, refresh depends on a dedicated HttpOnly session-binding cookie rather than IP/User-Agent lockstep, and auth rate limiting is now DB-backed through `auth_rate_limit_events`. Header-based bearer auth still exists for non-browser clients and API-style tests. Browser pytest still needs to run serially because `frontend/tests/conftest.py` shares `frontend_e2e.db`.

## Last updated
2026-03-23 00:37 UTC
