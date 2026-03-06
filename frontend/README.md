# webapp-boilerplate Frontend

Modern React + TypeScript frontend for the webapp-boilerplate authentication and user management system.

## Table of Contents

- [Features](#features)
  - [Authentication](#authentication)
  - [User Interface](#user-interface)
  - [Security Features](#security-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Development](#development)
  - [Build for Production](#build-for-production)
  - [Run Tests](#run-tests)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Routes](#routes)
- [Authentication Flow](#authentication-flow)
  - [Login](#login)
  - [Authenticated Requests](#authenticated-requests)
  - [Token Refresh](#token-refresh)
  - [Logout](#logout)
- [Multilingual Support](#multilingual-support)
- [Security Best Practices](#security-best-practices)
- [Development](#development-1)
  - [Available Scripts](#available-scripts)
  - [Code Style](#code-style)
  - [Adding New Pages](#adding-new-pages)
  - [API Integration](#api-integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Related Documentation](#related-documentation)

## Features

### Authentication
- **User Registration** with email validation and strong password requirements
- **Login/Logout** with JWT token-based authentication
- **Secure Session Management** with automatic token refresh
- **Proper Logout** - Notifies backend to revoke refresh tokens

### User Interface
- **Dashboard** - User homepage with quick links
- **User Profile** - View and manage user information
- **User Management** (Admin only) - Manage all users, activate/deactivate accounts
- **Multilingual Support** - UI labels in multiple languages with translation submission

### Security Features
- Access tokens stored in localStorage (short-lived)
- Refresh tokens in HttpOnly cookies (long-lived)
- Automatic token refresh on expiry
- Backend notification on logout for token revocation
- Protected routes requiring authentication
- Admin-only routes with role-based access control

## Tech Stack

- **React 19** - Modern React with hooks
- **TypeScript** - Type-safe development
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors
- **Tailwind CSS** - Utility-first styling
- **Chakra UI** - Component library
- **Vite** - Fast build tool and dev server
- **Vitest** - Unit testing framework

## Getting Started

### Prerequisites
- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will run on `http://localhost:5173` by default.

### Build for Production

```bash
npm run build
```

Outputs optimized build to `dist/` directory.

### Run Tests

#### Unit/Component Tests (Vitest)

```bash
npm test
```

Runs frontend unit and component tests for routes, API helpers, components, and context providers.

#### End-to-End Tests (Python/Playwright)

The supported browser-level test for this boilerplate is:
- `frontend/tests/test_setup_initialization_e2e.py`

It exercises the first-run setup flow, locale switching, admin settings locale updates, and responsive login/setup screens.

To run it:
```bash
cd backend
.venv/bin/pip install playwright
.venv/bin/playwright install --with-deps chromium
PYTHONPATH=. .venv/bin/pytest ../frontend/tests/test_setup_initialization_e2e.py -q
```

The test suite starts the backend and frontend automatically.

#### Visual Review Artifacts (Screenshots + Checklist)

Playwright E2E tests can now emit visual artifacts per test:
- step screenshots captured from the test flow,
- automatic failure screenshot on assertion failure,
- UX checklist scaffold for manual review.

Artifacts are written to:
- `frontend/tests/artifacts/<test_name>/`

Each folder contains:
- `*.png` screenshots,
- `ux_checklist.md` with review points (labels clarity, layout consistency, flow correctness, sensitive-field masking).

Responsive visual coverage includes explicit mobile and desktop snapshots in:
- `frontend/tests/test_setup_initialization_e2e.py::test_mobile_first_setup_and_login_visuals`

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   ├── api.ts        # Axios instance with interceptors
│   │   ├── auth.ts       # Authentication API calls
│   │   ├── types.ts      # TypeScript type definitions
│   │   └── uiLabel.ts    # Multilingual labels API
│   ├── components/       # React components
│   │   ├── Dashboard.tsx           # User dashboard
│   │   ├── Login.tsx               # Login page
│   │   ├── Register.tsx            # Registration page
│   │   ├── RequireAuth.tsx         # Protected route wrapper
│   │   ├── UiLabel.tsx             # Multilingual label component
│   │   ├── UserManagement.tsx      # Admin user management
│   │   └── UserProfile.tsx         # User profile page
│   ├── contexts/         # React contexts
│   │   ├── AuthContext.tsx         # Authentication state
│   │   └── UiLabelProvider.tsx     # Multilingual labels
│   ├── hooks/            # Custom React hooks
│   │   ├── useKeepUserLoggedIn.ts  # Auto token refresh
│   │   └── useT.ts                 # Translation hook
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component with routing
│   └── main.tsx          # App entry point
├── public/               # Static assets
├── tests/                # E2E tests (Python/Playwright)
└── package.json          # Dependencies and scripts
```

## Environment Variables

Copy `.env.example` to `.env` in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_BACKEND_POLL_INTERVAL=10000
```

- `VITE_API_URL` - Backend API URL
- `VITE_BACKEND_POLL_INTERVAL` - Backend reachability poll interval in milliseconds

## Routes

| Route | Component | Auth Required | Admin Only | Description |
|-------|-----------|---------------|------------|-------------|
| `/` | Dashboard | ✅ | ❌ | Redirects to dashboard |
| `/register` | Register | ❌ | ❌ | User registration |
| `/login` | Login | ❌ | ❌ | User login |
| `/setup` | SetupWizard | ❌ | ❌ | One-time first-run initialization |
| `/dashboard` | Dashboard | ✅ | ❌ | User homepage |
| `/profile` | UserProfile | ✅ | ❌ | User profile management |
| `/users` | UserManagement | ✅ | ✅ | Admin user management |

## First-run initialization

On a fresh deployment, the app is in setup mode:
- most routes are gated until setup is complete,
- users are redirected to `/setup`,
- backend setup submission requires a manually entered setup token.

Set the backend deploy secret `INITIAL_SETUP_TOKEN`, then complete `/setup` in the UI to initialize:
- site name and locale settings,
- initial admin email/password.

## Authentication Flow

### Login
1. User enters email and password
2. Frontend calls `/auth/token` endpoint
3. Backend returns access token (JWT) in response body
4. Backend sets refresh token in HttpOnly cookie
5. Frontend stores access token in localStorage
6. User redirected to dashboard

### Authenticated Requests
1. Axios interceptor adds `Authorization: Bearer <token>` header
2. Backend validates token and processes request

### Token Refresh
1. When access token expires (401 response)
2. Axios interceptor automatically calls `/auth/refresh`
3. Backend validates refresh token from cookie
4. Backend returns new access token
5. Interceptor retries original request with new token

### Logout
1. User clicks logout button
2. Frontend calls `/auth/logout` endpoint
3. Backend revokes refresh token and descendants
4. Frontend clears access token from localStorage
5. User redirected to login page

## Multilingual Support

The app uses a dynamic UI label system:

```tsx
import UiLabel from './components/UiLabel';

// In your component
<UiLabel k="nav.title.dashboard" />
```

Labels are:
- Loaded from backend on app start
- Cached in React context
- Users can suggest translations
- Admins can approve translations
- Document direction switches automatically for RTL locales (for example `ar` -> `dir="rtl"`)

## Security Best Practices

✅ **Implemented:**
- Access tokens in localStorage (short-lived, convenient for API calls)
- Refresh tokens in HttpOnly cookies (secure, long-lived)
- Automatic token refresh
- Proper logout with backend notification
- Protected routes with RequireAuth wrapper
- Role-based access control (admin vs regular user)
- Input validation on all forms
- Type-safe API calls with TypeScript

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run tests

### Code Style

- TypeScript for type safety
- Functional components with hooks
- ESLint for code quality
- Consistent naming conventions

### Adding New Pages

1. Create component in `src/components/`
2. Add route in `src/App.tsx`
3. Wrap with `<RequireAuth>` if authentication required
4. Add navigation link in App.tsx nav

### API Integration

Use the existing API client:

```typescript
import api from '../api/api';

// GET request
const response = await api.get('/endpoint');

// POST request
const response = await api.post('/endpoint', { data });
```

The API client automatically:
- Adds authentication headers
- Handles token refresh
- Retries failed requests

## Troubleshooting

**Issue:** Cannot connect to backend
- **Solution:** Check `VITE_API_BASE_URL` in `.env`
- **Solution:** Ensure backend is running on specified URL

**Issue:** Logout doesn't work
- **Solution:** Check browser console for API errors
- **Solution:** Verify backend `/auth/logout` endpoint is accessible

**Issue:** Token refresh fails
- **Solution:** Check cookies are enabled in browser
- **Solution:** Verify CORS configuration allows credentials

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Add proper error handling
4. Update this README if adding major features

## License

See LICENSE file in project root.

## Related Documentation

- `../SECURITY.md` - Security features and best practices
- `../AUTHENTICATION_FLOW.md` - Detailed authentication flow
- `../README.md` - Project overview
