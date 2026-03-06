import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import UserManagement from './UserManagement';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api/api.ts';

vi.mock('../api/api.ts');

vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

type AuthState = {
  token: string | null;
  user: { is_admin: boolean } | null;
};

function renderUserManagement(auth: AuthState) {
  const authValue = {
    token: auth.token,
    user: auth.user as any,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    setToken: vi.fn(),
  };

  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={['/users']}>
        <Routes>
          <Route path="/users" element={<UserManagement />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe('UserManagement Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('redirects non-admin users away from /users', () => {
    renderUserManagement({
      token: 'token-123',
      user: { is_admin: false },
    });

    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
  });

  it('loads and renders users for admin', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          id: 'u1',
          email: 'user1@example.com',
          is_active: true,
          is_admin: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
    } as any);

    renderUserManagement({
      token: 'token-123',
      user: { is_admin: true },
    });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/users', {
        headers: { Authorization: 'Bearer token-123' },
      });
    });

    expect(screen.getByText('user1@example.com')).toBeInTheDocument();
    expect(screen.getByText('user_management.action.deactivate')).toBeInTheDocument();
  });

  it('shows a non-blocking empty-state row when users fetch fails', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('request failed'));

    renderUserManagement({
      token: 'token-123',
      user: { is_admin: true },
    });

    await waitFor(() => {
      expect(screen.getByText('user_management.message.no_users_found')).toBeInTheDocument();
    });
  });

  it('toggles user active status and updates row action label', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          id: 'u1',
          email: 'user1@example.com',
          is_active: true,
          is_admin: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
    } as any);
    vi.mocked(api.put).mockResolvedValue({ data: {} } as any);

    renderUserManagement({
      token: 'token-123',
      user: { is_admin: true },
    });

    const deactivateButton = await screen.findByRole('button', {
      name: 'user_management.action.deactivate',
    });
    fireEvent.click(deactivateButton);

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith(
        '/users/u1',
        { is_active: false },
        { headers: { Authorization: 'Bearer token-123' } }
      );
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'user_management.action.activate' })).toBeInTheDocument();
    });
  });
});
