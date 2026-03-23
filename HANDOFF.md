# HANDOFF

## Current objective
Keep the hardened auth stack and deployment guidance stable. The repo now documents backend/database production paths plus the required frontend host and reverse-proxy edge behavior for cookie-backed browser auth.

## Completed in this session
- Added exact production edge guidance to `DEPLOYMENT.md` for the recommended `app.example.com` plus `api.example.com` layout, including the environment-variable matrix, CSP requirements, CORS constraints, same-site cookie notes, and HTTPS checklist.
- Added `deploy/nginx.frontend.conf.example` for static SPA hosting with the current required frontend CSP and client-side-route handling.
- Added `deploy/nginx.api.conf.example` for HTTPS redirect plus backend reverse proxy forwarding headers.
- Updated `README.md` to mention the new frontend-host/API-proxy deployment examples.
- Extended `backend/tests/scripts/test_deployment_examples.py` to keep the new Nginx examples and key directives under regression coverage.
- Verified the new deployment examples with `PYTHONPATH=. backend/.venv/bin/pytest backend/tests/scripts/test_deployment_examples.py -q` (`5 passed`).

## Current status
Browser auth is cookie-backed and no longer depends on `localStorage` bearer tokens. Refresh uses a dedicated session-binding cookie instead of IP/User-Agent enforcement, unsafe cookie-authenticated requests require a trusted `Origin` or `Referer`, backend responses emit a single default CSP, auth throttling is stored in the database rather than a process-local dict, and the backend supports SQLite plus PostgreSQL through a shared DB URL resolver. Deployment docs now cover SQLite, PostgreSQL, and the real frontend/API edge split with concrete Nginx examples. Focused deployment regression coverage is green from the current tree: `5` deployment-example tests passed, and the prior full backend verification state was `190` tests passed.

## Next step
Next meaningful step is deployment validation: add an executable smoke path that builds the frontend and checks the documented frontend-host/API-proxy topology end to end, so the new edge examples are validated beyond static file assertions.

## Important files
- AGENTS.md
- HANDOFF.md
- AUTHENTICATION_FLOW.md
- DEPLOYMENT.md
- README.md
- frontend/README.md
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
The production docs now assume the preferred browser-auth topology is `https://app.example.com` plus `https://api.example.com`, with `COOKIE_SAME_SITE=lax` and exact `CORS_ALLOW_ORIGINS`. `DEPLOYMENT.md` now explains when that assumption breaks, especially for cross-site frontend/backend splits that would require `COOKIE_SAME_SITE=none`. The new Nginx examples are documentation artifacts only; they are covered by focused static assertions in `backend/tests/scripts/test_deployment_examples.py`. Header-based bearer auth still exists for non-browser clients and API-style tests. Browser pytest still needs to run serially because `frontend/tests/conftest.py` shares `frontend_e2e.db`.

## Last updated
2026-03-23 01:09 UTC
