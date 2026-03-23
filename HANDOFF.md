# HANDOFF

## Current objective
Keep the hardened auth stack and deployment guidance stable, with the project documentation matching the current auth, frontend, test, and deployment behavior.

## Completed in this session
- Updated `AUTHENTICATION_FLOW.md` to match the current auth stack: bcrypt-with-SHA256 prehash wording, 14-day refresh default, cookie/body token behavior, and the exact CSRF model.
- Updated `frontend/README.md` to match the current frontend routes, browser test suite, project structure, setup/navigation ownership, and `VITE_API_URL` naming.
- Updated `backend/tests/README.md` to document the existing `tests/scripts` and `tests/ai` suites and to use the repo’s current virtualenv-backed helper command style.
- Updated `CONTRIBUTING.md` verification guidance to the repo-standard `make verify-backend` plus the current frontend/browser verification paths.
- Ran `git diff --check` successfully after the doc updates.

## Current status
Browser auth is cookie-backed and no longer depends on `localStorage` bearer tokens. Refresh uses a dedicated session-binding cookie instead of IP/User-Agent enforcement, unsafe cookie-authenticated requests require a trusted `Origin` or `Referer`, backend responses emit a single default CSP, auth throttling is stored in the database rather than a process-local dict, and the backend supports SQLite plus PostgreSQL through a shared DB URL resolver. The main auth/frontend/test docs now reflect those realities instead of older assumptions about token lifetimes, route ownership, or frontend test coverage. The last focused automated check in this session was `git diff --check`; the prior deployment-example regression state remained `5 passed`, and the prior full backend verification state remained `190` tests passed.

## Next step
Next meaningful step is deployment validation: add an executable smoke path that builds the frontend and checks the documented frontend-host/API-proxy topology end to end, so the new edge examples are validated beyond static file assertions.

## Important files
- AGENTS.md
- HANDOFF.md
- AUTHENTICATION_FLOW.md
- CONTRIBUTING.md
- DEPLOYMENT.md
- README.md
- frontend/README.md
- backend/tests/README.md
- backend/tests/scripts/test_deployment_examples.py
- backend/Dockerfile
- deploy/docker-compose.sqlite.yml
- deploy/docker-compose.postgres.yml
- deploy/backend.sqlite.env.example
- deploy/backend.postgres.env.example
- deploy/postgres.env.example
- deploy/nginx.frontend.conf.example
- deploy/nginx.api.conf.example

## Notes for next session
The production docs assume the preferred browser-auth topology is `https://app.example.com` plus `https://api.example.com`, with `COOKIE_SAME_SITE=lax` and exact `CORS_ALLOW_ORIGINS`. `DEPLOYMENT.md` explains when that assumption breaks, especially for cross-site frontend/backend splits that would require `COOKIE_SAME_SITE=none`. Header-based bearer auth still exists for non-browser clients and API-style tests. Browser pytest still needs to run serially because `frontend/tests/conftest.py` shares `frontend_e2e.db`. The recent documentation sweep aligned auth/session details, frontend routes/test files, and contributor verification commands with the current codebase.

## Last updated
2026-03-23 01:31 UTC
