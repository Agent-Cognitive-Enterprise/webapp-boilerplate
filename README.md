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
- [Environment Variables](#environment-variables)
- [Common Commands](#common-commands)
- [One-Command Development](#one-command-development)
- [API Surface (High Level)](#api-surface-high-level)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Highlights

- FastAPI backend with async SQLModel/SQLAlchemy + SQLite
- React 19 + TypeScript frontend (Vite)
- First-run initialization flow (`/setup`) protected by one-time setup token
- JWT access tokens + rotating refresh tokens in HttpOnly cookies
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
- `DB_TYPE` (currently `sqlite`)
- `SQLITE_DB_PATH` (default: `app.db`)
- `AUTH_SECRET_KEY` (required)
- `INITIAL_SETUP_TOKEN` (required)
- `CORS_ALLOW_ORIGINS` (default: `http://localhost:5173`)
- `AUTH_FRONTEND_BASE_URL` (default: `http://localhost:5173`)
- `AUTH_BACKEND_BASE_URL` (default: `http://localhost:8000`)
- `COOKIE_SAME_SITE` / `COOKIE_SECURE`
- `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` (optional third-party AI provider keys)

See [backend/.env.example](backend/.env.example) for the full template.

### Frontend (`frontend/.env`)

- `VITE_API_URL` (default: `http://localhost:8000`)
- `VITE_BACKEND_POLL_INTERVAL` (default: `10000`)

See [frontend/.env.example](frontend/.env.example).

## Common Commands

### Backend

```bash
cd backend
source .venv/bin/activate

# run all backend tests
PYTHONPATH=. pytest -q

# run backend e2e tests
PYTHONPATH=. pytest tests/e2e -q

# run i18n audit
PYTHONPATH=. python scripts/i18n_audit.py
```

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

This prints the two commands to run in separate terminals:

- `make backend-dev`
- `make frontend-dev`

## API Surface (High Level)

- Health: `GET /health`
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
