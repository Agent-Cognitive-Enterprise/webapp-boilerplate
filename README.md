# webapp-boilerplate

Open-source full-stack boilerplate for building secure, multilingual web applications.

It includes a FastAPI backend and React + TypeScript frontend with authentication, first-run setup flow, admin settings, user management, and test coverage across backend and frontend.

## Disclaimer
This project is provided "AS IS", without warranties or conditions of any kind.
To the maximum extent permitted by law, the authors and contributors are not liable for any damages arising from its use.
See the LICENSE file (Apache License 2.0) for the full terms.

## Table of Contents

- [Highlights](#highlights)
- [Tech Stack](#tech-stack)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Common Commands](#common-commands)
- [One-Command Development](#one-command-development)
- [API Surface (High Level)](#api-surface-high-level)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Highlights

- FastAPI backend with async SQLModel/SQLAlchemy
- SQLite support for local development and small single-node deployments
- PostgreSQL support for standard production deployments
- Deployment examples for SQLite single-node and PostgreSQL-backed production
- React 19 + TypeScript frontend (Vite)
- First-run initialization flow (`/setup`) protected by one-time setup token
- JWT access tokens + rotating refresh tokens with HttpOnly session-binding cookies
- Email verification and password reset flows
- Admin user management and system settings endpoints
- Dynamic UI labels with locale support including RTL locales
- Alembic migrations and backend/frontend test suites

## Tech Stack

### Backend
- Python
- FastAPI
- SQLModel + SQLAlchemy (async)
- Alembic
- JWT (`python-jose`) + `passlib`

### Frontend
- React 19
- TypeScript
- Vite
- React Router
- Axios
- Tailwind CSS + Chakra UI
- Vitest + Testing Library

## Repository Layout

```text
.
├── backend/           # FastAPI app, models, auth, migrations, tests
├── frontend/          # React app, components, hooks, tests
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── AUTHENTICATION_FLOW.md
├── SECURITY.md
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Set at least these required values in `backend/.env`:

- `AUTH_SECRET_KEY`
- `INITIAL_SETUP_TOKEN`

Optional AI provider keys:

- `OPENAI_API_KEY` for OpenAI-backed translation/suggestion features
- `DEEPSEEK_API_KEY` for DeepSeek-backed translation/suggestion features

Generate a strong secret, for example:

```bash
openssl rand -hex 32
```

Run migrations and start backend:

```bash
alembic upgrade head
python main.py
```

Backend runs on `http://localhost:8000`.
Direct `python main.py` runs perform a startup migration preflight only in these cases:

- `APP_ENV=development` or `APP_ENV=dev`
- `AUTO_MIGRATE_ON_START=true`
- `AUTO_MIGRATE_ON_START=auto` with SQLite and a missing DB file

Set `AUTO_MIGRATE_ON_START=false` to disable that preflight. Import-based server paths such as `uvicorn main:app` do not auto-migrate; run `alembic upgrade head` yourself before serving traffic in those paths.

Database choices:

- SQLite is the default local setup via `SQLITE_DB_PATH`.
- SQLite can also be used in small single-node production deployments.
- PostgreSQL is the recommended production backend. Set `DATABASE_URL`, for example `postgresql://user:pass@localhost:5432/webapp`.

### 3. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs on `http://localhost:5173`.

### 4. Complete First-Run Setup

On fresh startup, the app is locked until setup is completed:

1. Open `http://localhost:5173/setup`
2. Enter the `INITIAL_SETUP_TOKEN` from `backend/.env`
3. Configure initial app settings and admin account

## Environment Variables

### Backend (`backend/.env`)

Core variables:

- `APP_ENV` (default: `development`)
- `DATABASE_URL` (recommended for PostgreSQL and other non-default deployments)
- `DB_TYPE` (compatibility fallback; default: `sqlite`)
- `SQLITE_DB_PATH` (default: `app.db`)
- `AUTO_MIGRATE_ON_START` (`auto|true|false`, default: `auto`)
- `AUTH_SECRET_KEY` (required)
- `INITIAL_SETUP_TOKEN` (required)
- `CORS_ALLOW_ORIGINS` (default: `http://localhost:5173`)
- `AUTH_FRONTEND_BASE_URL` (default: `http://localhost:5173`)
- `AUTH_BACKEND_BASE_URL` (default: `http://localhost:8000`)
- `COOKIE_SAME_SITE` / `COOKIE_SECURE`
- `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` (optional third-party AI provider keys)
- `UI_LABEL_BACKGROUND_TASKS_ENABLED` (default: `true`; set `false` in automated environments to disable background UI-label translation/suggestion jobs)

See [backend/.env.example](backend/.env.example) for the full template.

Database support:

- SQLite remains supported for local development and small single-node production deployments.
- PostgreSQL is supported and recommended for standard production deployments.
- The application resolves both runtime and Alembic database URLs from the same environment settings.
- Direct `python main.py` runs normalize relative SQLite paths before preflight so Alembic and the app target the same DB file.
- If the schema is missing or out of date at runtime, `GET /health` returns `503` with a migration hint instead of throwing an internal traceback.

### Frontend (`frontend/.env`)

- `VITE_API_URL` (default: `http://localhost:8000`)
- `VITE_BACKEND_POLL_INTERVAL` (default: `10000`)

See [frontend/.env.example](frontend/.env.example).

## Deployment

For supported production topologies and concrete deployment examples, see [DEPLOYMENT.md](DEPLOYMENT.md).

Summary:

- SQLite is still a valid production path for small single-node deployments.
- PostgreSQL is the recommended path for standard production deployments.
- The deployment examples cover backend plus database, and include Nginx examples for the production frontend host and API reverse proxy.

## Common Commands

### Backend

```bash
cd backend
source .venv/bin/activate

# run all backend tests
PYTHONPATH=. pytest -q

# check CI test-env drift
python scripts/check_ci_test_env.py

# run backend lint
.venv/bin/ruff check .

# run backend type checks
PYTHONPATH=. .venv/bin/mypy --config-file pyproject.toml

# run backend e2e tests
PYTHONPATH=. pytest tests/e2e -q

# run deployment smoke validation
.venv/bin/python scripts/smoke_deployment_topology.py

# run i18n audit
PYTHONPATH=. python scripts/i18n_audit.py
```

From the repository root, the default backend verification path is:

```bash
make verify-backend
```

The backend `mypy` gate is currently scoped to the typed backend verification path configured in `backend/pyproject.toml`:
- `crud/`
- `services/bootstrap.py`
- `services/email_service.py`
- `services/system_settings.py`
- `services/ui_label_seed.py`
- `auth/cookies.py`
- `scripts/check_email_config.py`
- `scripts/check_env_email_settings.py`

For the documented production frontend host plus API proxy topology, run:

```bash
make smoke-deployment
```

That command performs a real frontend production build with `VITE_API_URL=https://api.example.com` and validates the generated `frontend/dist/` output plus the Nginx example configs.

Test auth/setup defaults used by backend tests and frontend browser tests are centralized in `backend/tests/test_env.py`. Do not duplicate `AUTH_SECRET_KEY` or `INITIAL_SETUP_TOKEN` in CI test-job `env` blocks; `backend/scripts/check_ci_test_env.py` enforces that rule.

### Frontend

```bash
cd frontend

# dev server
npm run dev

# unit/component tests
npm test

# lint
npm run lint

# production build
npm run build
```

## One-Command Development

From the repository root:

```bash
make dev
```

This prints the commands to run:

- `make backend-migrate`
- `make backend-dev`
- `make frontend-dev`

## API Surface (High Level)

- Health: `GET /health` (`503` with a migration hint when the DB schema is missing or out of date)
- Setup: `GET /setup/status`, `POST /setup`, `POST /setup/email/check`
- Auth: `POST /auth/register`, `POST /auth/token`, `POST /auth/refresh`, `POST /auth/logout`
- Password reset: `POST /auth/forgot-password`, `POST /auth/reset-password`
- Email verification: `GET /auth/verify-email`
- Users: `GET /users/me/`, admin CRUD on `/users`
- Admin settings: `GET /admin/settings`, `PUT /admin/settings`

For full auth behavior and security flow details, see [AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md).

## Security

- Review [SECURITY.md](SECURITY.md) for policy and reporting guidance.
- Never commit secrets (`.env`, API keys, SMTP passwords).
- In production, set `COOKIE_SECURE=true` and use HTTPS.
- Malformed JSON request bodies now return `400 Bad Request`; schema validation errors still return `422`.
- Backend responses include CSP and clickjacking headers, and emit HSTS when the request reaches the app as HTTPS.
- The Vite dev/preview host also emits CSP, clickjacking, and HSTS headers for SPA routes so local/browser verification sees the same baseline protections.
- This repository does not serve the Vite frontend from FastAPI in production, so deploy the same CSP intent at the frontend host or reverse proxy as well.
- Repository automation included:
  - CI: `.github/workflows/ci.yml`
  - CodeQL: `.github/workflows/codeql.yml`
  - Secret scanning (Gitleaks): `.github/workflows/secret-scan.yml`
  - OpenSSF Scorecard: `.github/workflows/scorecard.yml`
  - Dependabot: `.github/dependabot.yml`
- Repository settings to enable in GitHub UI:
  - Secret Scanning + Push Protection
  - Branch protection on `main` (required status checks + required PR review)
  - Private vulnerability reporting

## Contributing

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
2. Create a feature branch.
3. Add or update tests for your change.
4. Run backend and frontend test suites.
5. Open a pull request with clear scope and rationale.

## License

Licensed under Apache 2.0. See [LICENSE](LICENSE).
