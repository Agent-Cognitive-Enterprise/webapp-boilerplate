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

## Backend image

The backend container image is defined in `backend/Dockerfile`.

It expects you to:

1. provide environment variables
2. run Alembic migrations before or during startup
3. expose the app behind HTTPS in real production

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

## Production checklist

- Set `APP_ENV=production`
- Set `COOKIE_SECURE=true`
- Use HTTPS at the edge
- Replace all placeholder secrets
- Run with persistent storage
- Apply the frontend CSP at the real frontend host or reverse proxy
- Complete `/setup` after first boot using `INITIAL_SETUP_TOKEN`
