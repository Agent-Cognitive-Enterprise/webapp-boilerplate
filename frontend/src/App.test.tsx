import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { AuthContext } from './contexts/AuthContext';
import { getSetupStatus } from './api/setup';
import { fetchPublicBranding } from './api/appConfig';

vi.mock('./hooks/useKeepUserLoggedIn.ts', () => ({
  useKeepUserLoggedIn: vi.fn(),
}));

vi.mock('./api/setup.ts', () => ({
  getSetupStatus: vi.fn(),
}));
vi.mock('./api/appConfig.ts', () => ({
  fetchPublicBranding: vi.fn(),
}));
vi.mock('./hooks/useT.ts', () => ({
  useT: (_k: string, _fillers?: Record<string, string>, fallback?: string) => fallback ?? _k,
}));

vi.mock('./components/UiLabel.tsx', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

vi.mock('./components/Register.tsx', () => ({ default: () => <div>Register Page</div> }));
vi.mock('./components/Login.tsx', () => ({ default: () => <div>Login Page</div> }));
vi.mock('./components/UserProfile.tsx', () => ({ default: () => <div>Profile Page</div> }));
vi.mock('./components/Dashboard.tsx', () => ({ default: () => <div>Dashboard Page</div> }));
vi.mock('./components/UserManagement.tsx', () => ({ default: () => <div>User Management Page</div> }));
vi.mock('./components/ForgotPassword.tsx', () => ({ default: () => <div>Forgot Password Page</div> }));
vi.mock('./components/ResetPassword.tsx', () => ({ default: () => <div>Reset Password Page</div> }));
vi.mock('./components/AdminSettings.tsx', () => ({ default: () => <div>Admin Settings Page</div> }));

type AuthState = {
  token: string | null;
  user: { is_admin: boolean } | null;
};

function renderApp(auth: AuthState, initialRoute = '/') {
  const logout = vi.fn();
  const authValue = {
    token: auth.token,
    user: auth.user as any,
    login: vi.fn(),
    register: vi.fn(),
    logout,
    setToken: vi.fn(),
  };

  const utils = render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <App />
      </MemoryRouter>
    </AuthContext.Provider>
  );

  return { ...utils, logout };
}

describe('App routing and navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.mocked(getSetupStatus).mockResolvedValue({ is_initialized: true });
    vi.mocked(fetchPublicBranding).mockResolvedValue({ appName: 'ACE', siteLogo: null, backgroundImage: null });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows guest nav links for unauthenticated users', async () => {
    renderApp({ token: null, user: null }, '/login');
    await waitFor(() => expect(screen.getByRole('link', { name: 'nav.title.register' })).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'nav.title.login' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'nav.title.logout' })).not.toBeInTheDocument();
  });

  it('redirects unauthenticated access to protected route /dashboard -> /login', async () => {
    renderApp({ token: null, user: null }, '/dashboard');
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());
  });

  it('shows authenticated nav links and protected page for regular user', async () => {
    renderApp({ token: 'token-123', user: { is_admin: false } }, '/dashboard');

    await waitFor(() => expect(screen.getByRole('link', { name: 'nav.title.dashboard' })).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'nav.title.profile' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'nav.title.logout' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'nav.title.users' })).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Dashboard Page')).toBeInTheDocument());
  });

  it('shows admin users nav link for admin user', async () => {
    renderApp({ token: 'token-123', user: { is_admin: true } }, '/dashboard');
    await waitFor(() => expect(screen.getByRole('link', { name: 'nav.title.users' })).toBeInTheDocument());
    expect(screen.getByRole('link', { name: 'nav.title.admin_settings' })).toBeInTheDocument();
  });

  it('calls logout from nav button', async () => {
    const { logout } = renderApp({ token: 'token-123', user: { is_admin: false } }, '/dashboard');
    await waitFor(() => expect(screen.getByRole('button', { name: 'nav.title.logout' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'nav.title.logout' }));
    expect(logout).toHaveBeenCalledTimes(1);
  });

  it('forces /setup for uninitialized app', async () => {
    vi.mocked(getSetupStatus).mockResolvedValue({ is_initialized: false });
    renderApp({ token: null, user: null }, '/dashboard');

    await waitFor(() => expect(screen.getByText('First-Run Setup')).toBeInTheDocument());
    expect(screen.queryByText('Dashboard Page')).not.toBeInTheDocument();
  });

  it('shows backend offline overlay before setup when backend is unreachable', async () => {
    vi.mocked(getSetupStatus).mockRejectedValue(new Error('network down'));
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    renderApp({ token: null, user: null }, '/setup');

    await waitFor(() => expect(screen.getByText('Backend is offline')).toBeInTheDocument());
    expect(screen.getByText('Cannot reach backend service. Start backend and refresh this page.')).toBeInTheDocument();
  });

  it('applies rtl document direction when ui locale is arabic', async () => {
    localStorage.setItem('uiLocale', 'ar');
    renderApp({ token: null, user: null }, '/login');
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());
    expect(document.documentElement.lang).toBe('ar');
    expect(document.documentElement.dir).toBe('rtl');
  });

  it('keeps ltr document direction when ui locale is english', async () => {
    localStorage.setItem('uiLocale', 'en');
    renderApp({ token: null, user: null }, '/login');
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());
    expect(document.documentElement.lang).toBe('en');
    expect(document.documentElement.dir).toBe('ltr');
  });

  it('uses cached custom background immediately on refresh, without showing default first', async () => {
    localStorage.setItem('branding.backgroundImage', 'data:image/png;base64,CACHED_BG');
    let resolveBranding: ((value: { appName: string; siteLogo: string | null; backgroundImage: string | null }) => void) | null = null;
    vi.mocked(fetchPublicBranding).mockReturnValue(
      new Promise((resolve) => {
        resolveBranding = resolve;
      }) as any
    );

    renderApp({ token: null, user: null }, '/login');
    await waitFor(() => expect(screen.getByText('Login Page')).toBeInTheDocument());

    const bgContainer = screen.getByTestId('app-background-shell') as HTMLDivElement | null;
    expect(bgContainer).not.toBeNull();
    expect(bgContainer!.style.backgroundImage).toContain('CACHED_BG');

    resolveBranding?.({ appName: 'ACE', siteLogo: null, backgroundImage: 'data:image/png;base64,SERVER_BG' });
    await waitFor(() => expect(bgContainer!.style.backgroundImage).toContain('SERVER_BG'));
  });

});
