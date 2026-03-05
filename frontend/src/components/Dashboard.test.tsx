import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from "react-router-dom";
import Dashboard from './Dashboard';
import { AuthContext } from '../contexts/AuthContext';

vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

function renderDashboard(isAdmin: boolean) {
  const authValue = {
    token: 'token-123',
    user: {
      full_name: 'Test User',
      email: 'user@example.com',
      id: 'u1',
      is_admin: isAdmin,
      is_active: true,
    },
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    setToken: vi.fn(),
  };

  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <Dashboard />
      </AuthContext.Provider>
    </MemoryRouter>
  );
}

describe('Dashboard Component', () => {
  it('renders user email and common links', () => {
    renderDashboard(false);
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'dashboard.link.view_profile' })).toHaveAttribute('href', '/profile');
    expect(screen.queryByRole('link', { name: 'dashboard.link.manage_users' })).not.toBeInTheDocument();
  });

  it('renders admin users link for admin', () => {
    renderDashboard(true);
    expect(screen.getByRole('link', { name: 'dashboard.link.manage_users' })).toHaveAttribute('href', '/users');
  });
});
