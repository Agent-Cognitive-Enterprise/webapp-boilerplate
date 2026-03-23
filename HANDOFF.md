# HANDOFF

## Current objective
Keep the hardened auth stack and deployment guidance stable, with deployment examples backed by an executable smoke path instead of documentation-only assertions.

## Completed in this session
- Removed the unused `sys` import from `backend/scripts/smoke_deployment_topology.py` after the GitHub Actions Ruff failure.
- Added `backend/scripts/smoke_deployment_topology.py`, an executable smoke script that rebuilds the frontend with the documented production `VITE_API_URL` and validates the generated `frontend/dist/` output plus the Nginx frontend/API examples together.
- Added focused regression coverage in `backend/tests/scripts/test_smoke_deployment_topology.py`.
- Added `make smoke-deployment` and documented it in `README.md`, `DEPLOYMENT.md`, and `CONTRIBUTING.md`.
- Re-ran deployment-focused regression coverage successfully with `PYTHONPATH=. backend/.venv/bin/pytest backend/tests/scripts/test_deployment_examples.py backend/tests/scripts/test_smoke_deployment_topology.py -q` (`8 passed`).
- Ran the real smoke path successfully with `make smoke-deployment`, which performed a production frontend build and passed the topology validation.
- Re-ran targeted lint successfully with `cd backend && .venv/bin/ruff check scripts/smoke_deployment_topology.py`.

## Current status
Browser auth is cookie-backed and no longer depends on `localStorage` bearer tokens. Refresh uses a dedicated session-binding cookie instead of IP/User-Agent enforcement, unsafe cookie-authenticated requests require a trusted `Origin` or `Referer`, backend responses emit a single default CSP, auth throttling is stored in the database rather than a process-local dict, and the backend supports SQLite plus PostgreSQL through a shared DB URL resolver. The deployment docs now have a matching executable validation path: `make smoke-deployment` rebuilds the frontend with `https://api.example.com`, checks the built output for the correct API origin, rejects the localhost fallback, and validates the documented frontend/API Nginx edge configs. Current deployment-focused regression coverage is `8` passing tests; the prior full backend verification state remained `190` tests passed.

## Next step
Next meaningful step is broader deployment automation: decide whether the smoke path should stay as a fast local/CI script or be extended into a containerized end-to-end deployment check that actually boots Nginx plus the backend together.

## Important files
- AGENTS.md
- HANDOFF.md
- AUTHENTICATION_FLOW.md
- CONTRIBUTING.md
- DEPLOYMENT.md
- README.md
- frontend/README.md
- backend/tests/README.md
- backend/scripts/smoke_deployment_topology.py
- backend/tests/scripts/test_deployment_examples.py
- backend/tests/scripts/test_smoke_deployment_topology.py
- backend/Dockerfile
- deploy/docker-compose.sqlite.yml
- deploy/docker-compose.postgres.yml
- deploy/backend.sqlite.env.example
- deploy/backend.postgres.env.example
- deploy/postgres.env.example
- deploy/nginx.frontend.conf.example
- deploy/nginx.api.conf.example

## Notes for next session
The production docs assume the preferred browser-auth topology is `https://app.example.com` plus `https://api.example.com`, with `COOKIE_SAME_SITE=lax` and exact `CORS_ALLOW_ORIGINS`. `DEPLOYMENT.md` explains when that assumption breaks, especially for cross-site frontend/backend splits that would require `COOKIE_SAME_SITE=none`. Header-based bearer auth still exists for non-browser clients and API-style tests. Browser pytest still needs to run serially because `frontend/tests/conftest.py` shares `frontend_e2e.db`. The new smoke script is intentionally fast and local: it does a real frontend build and validates the built artifacts/configs, but it does not boot Nginx or containers.

## Last updated
2026-03-23 01:49 UTC
