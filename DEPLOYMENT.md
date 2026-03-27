# Deployment

## Supported production paths

This repository supports two honest production shapes:

- SQLite on a single node with persistent local storage
- PostgreSQL for standard production deployments

SQLite remains a valid production path if you are running:

- one backend instance
- on durable storage
- with modest write concurrency
- without horizontal scaling requirements

PostgreSQL is the recommended default when you want:

- a more typical production topology
- cleaner scaling options later
- stronger operational separation between app and database

## Important constraint

The backend does not serve the Vite frontend in production.

That means every deployment path here covers the backend and database only. Deploy the frontend separately as a static build, and apply equivalent CSP headers at the frontend host or reverse proxy.

## Recommended host layout

The safest browser-auth topology for this repo is:

- frontend at `https://app.example.com`
- backend API at `https://api.example.com`

That keeps the browser session same-site while still separating the static frontend host from the API host.

Recommended production values for that layout:

| Setting | Value |
| --- | --- |
| `VITE_API_URL` | `https://api.example.com` |
| `CORS_ALLOW_ORIGINS` | `https://app.example.com` |
| `AUTH_FRONTEND_BASE_URL` | `https://app.example.com` |
| `AUTH_BACKEND_BASE_URL` | `https://api.example.com` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAME_SITE` | `lax` |

Notes:

- Keep `CORS_ALLOW_ORIGINS` to exact origins. Do not use `*` because browser auth requires `allow_credentials=True`.
- Leave `COOKIE_DOMAIN` unset unless you explicitly need wider cookie scope. Host-only cookies are the safer default.
- If the frontend and backend are on different registrable domains, `COOKIE_SAME_SITE=lax` will block cookie-authenticated XHR/fetch requests. In that case you must intentionally move to `COOKIE_SAME_SITE=none`, keep `COOKIE_SECURE=true`, and accept the broader CSRF surface.

## Backend image

The backend container image is defined in `backend/Dockerfile`.

It expects you to:

1. provide environment variables
2. run Alembic migrations before or during startup
3. expose the app behind HTTPS in real production

Direct `python main.py` runs are intentionally narrower than deployment server paths:

- in `APP_ENV=development` or `APP_ENV=dev`, the direct entrypoint runs `alembic upgrade head` before starting the server
- in production-like envs, the direct entrypoint skips auto-migration by default
- exception: with `AUTO_MIGRATE_ON_START=auto`, a missing SQLite DB file still triggers a direct-run preflight migration
- `AUTO_MIGRATE_ON_START=true` forces the preflight, and `AUTO_MIGRATE_ON_START=false` disables it

Import-based paths such as `uvicorn main:app` do not auto-migrate. Keep explicit migration steps in deployment automation, as the compose examples already do.

## SQLite deployment example

Files:

- `deploy/docker-compose.sqlite.yml`
- `deploy/backend.sqlite.env.example`

Why this path exists:

- it keeps SQLite as a supported production option
- it is appropriate for small single-node deployments
- it uses a persistent Docker volume for the database file

Setup:

1. Copy `deploy/backend.sqlite.env.example` to `deploy/backend.sqlite.env`
2. Replace all placeholder secrets and origin URLs
3. Run:

```bash
cd deploy
cp backend.sqlite.env.example backend.sqlite.env
docker compose -f docker-compose.sqlite.yml up --build -d
```

Notes:

- The SQLite database lives at `/data/app.db` inside the backend container.
- The named Docker volume `sqlite_data` is the persistence boundary.
- Do not scale this backend service horizontally while using SQLite.
- If schema drift still reaches runtime, `GET /health` returns `503` with a migration hint instead of an internal traceback.

## PostgreSQL deployment example

Files:

- `deploy/docker-compose.postgres.yml`
- `deploy/backend.postgres.env.example`
- `deploy/postgres.env.example`

Setup:

1. Copy `deploy/backend.postgres.env.example` to `deploy/backend.postgres.env`
2. Copy `deploy/postgres.env.example` to `deploy/postgres.env`
3. Replace all placeholder secrets, passwords, and origin URLs
4. Run:

```bash
cd deploy
cp backend.postgres.env.example backend.postgres.env
cp postgres.env.example postgres.env
docker compose -f docker-compose.postgres.yml up --build -d
```

Notes:

- The backend waits for PostgreSQL health before starting.
- The backend uses `DATABASE_URL=postgresql://...`; the app converts that to the async runtime driver automatically.
- The named Docker volume `postgres_data` persists the database state.
- If migrations are skipped or incomplete, `GET /health` returns `503` with a migration hint until the schema is corrected.

## Frontend deployment

Build the frontend with the correct backend URL:

```bash
cd frontend
npm install
VITE_API_URL=https://api.example.com npm run build
```

Deploy the generated `frontend/dist/` assets to your static host or reverse proxy.

Requirements:

- `VITE_API_URL` must point at the deployed backend URL
- `CORS_ALLOW_ORIGINS` must include the deployed frontend origin
- `AUTH_FRONTEND_BASE_URL` must match the frontend origin
- `AUTH_BACKEND_BASE_URL` must match the backend origin used in auth flows

Concrete Nginx examples for the frontend host and API reverse proxy are included here:

- `deploy/nginx.frontend.conf.example`
- `deploy/nginx.api.conf.example`

Smoke-check the documented topology from the repository root with:

```bash
make smoke-deployment
```

That command rebuilds the frontend with `VITE_API_URL=https://api.example.com` and validates:

- the generated `frontend/dist/` output references the production API origin
- the generated build no longer references the localhost API fallback
- the frontend Nginx config still matches the SPA/CSP requirements
- the API Nginx config still preserves the required HTTPS forwarding headers

Those examples assume:

- frontend static files are served from `frontend/dist/`
- the frontend host is `app.example.com`
- the backend host is `api.example.com`
- TLS is terminated at Nginx

## Frontend host requirements

The current frontend needs these CSP allowances at the real frontend host:

- `script-src 'self'`
- `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`
- `font-src 'self' data: https://fonts.gstatic.com`
- `img-src 'self' data: blob:`
- `connect-src 'self' https://api.example.com`

Why those directives are required today:

- `connect-src` must allow the deployed API origin because the browser talks directly to the backend.
- `style-src 'unsafe-inline'` is required by the current Chakra UI / Emotion runtime styling approach.
- `fonts.googleapis.com` and `fonts.gstatic.com` are required by the current frontend font import in `frontend/src/index.css`.
- `img-src data: blob:` covers the current branding image paths and browser-generated blob URLs.

If you remove Google Fonts or move away from Emotion-injected styles later, tighten the frontend CSP accordingly.

The frontend host should also:

- redirect HTTP to HTTPS
- emit HSTS after TLS is working
- serve `index.html` for client-side routes
- cache hashed assets aggressively
- avoid adding permissive CORS headers; the browser should load the SPA from the same origin it was requested from

## API reverse proxy requirements

The API reverse proxy should:

- redirect HTTP to HTTPS
- preserve `Host`
- send `X-Forwarded-For`, `X-Real-IP`, `X-Forwarded-Host`, and `X-Forwarded-Proto=https`
- avoid overwriting the backend `Content-Security-Policy` header
- avoid adding wildcard CORS headers in front of FastAPI

The backend already emits its own security headers and exact-origin CORS behavior. Preserve `X-Forwarded-Proto=https` so backend HSTS is emitted only for HTTPS requests, and let the proxy forward that response cleanly rather than trying to replace the app logic.

## HTTPS and edge checklist

For a production frontend host plus API host split, verify all of the following together:

- browser users load the SPA from `https://app.example.com`
- the SPA calls `https://api.example.com`
- `VITE_API_URL`, `CORS_ALLOW_ORIGINS`, `AUTH_FRONTEND_BASE_URL`, and `AUTH_BACKEND_BASE_URL` all match those public URLs exactly
- `COOKIE_SECURE=true`
- `COOKIE_SAME_SITE=lax` only if frontend and backend stay same-site
- HTTP is redirected to HTTPS on both hosts
- HSTS is enabled only after HTTPS is confirmed working
- the frontend host serves the frontend CSP
- the API proxy preserves forwarded headers and does not loosen CORS
- the backend origin exposed to browsers matches the origin used in emails and auth redirects

## Production checklist

- Set `APP_ENV=production`
- Set `COOKIE_SECURE=true`
- Use HTTPS at the edge
- Replace all placeholder secrets
- Run with persistent storage
- Apply the frontend CSP at the real frontend host or reverse proxy
- Use the included Nginx examples or mirror their HTTPS/CSP/CORS behavior at your real edge
- Complete `/setup` after first boot using `INITIAL_SETUP_TOKEN`
