import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import UserProfile from './UserProfile';
import { AuthContext } from '../contexts/AuthContext';

vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

vi.mock('./UiLocaleSelector', () => ({
  default: () => <div data-testid="locale-selector">Locale Selector</div>,
}));

describe('UserProfile Component', () => {
  it('shows loading when user is missing', () => {
    const authValue = {
      token: 'token-123',
      user: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      setToken: vi.fn(),
    };

    render(
      <AuthContext.Provider value={authValue}>
        <UserProfile />
      </AuthContext.Provider>
    );

    expect(screen.getByText('common.loading')).toBeInTheDocument();
  });

  it('renders user info and triggers logout', () => {
    const logout = vi.fn();
    const authValue = {
      token: 'token-123',
      user: {
        full_name: 'Jane Doe',
        email: 'jane@example.com',
        id: 'u1',
        is_admin: false,
        is_active: true,
      },
      login: vi.fn(),
      register: vi.fn(),
      logout,
      setToken: vi.fn(),
    };

    render(
      <AuthContext.Provider value={authValue}>
        <UserProfile />
      </AuthContext.Provider>
    );

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByTestId('locale-selector')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('logout-button'));
    expect(logout).toHaveBeenCalledTimes(1);
  });
});
