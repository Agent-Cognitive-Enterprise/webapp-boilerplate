// frontend/src/components/Login.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import { AuthContext } from '../contexts/AuthContext';

// Mock UiLabel component
vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span data-testid={`ui-label-${k}`}>{k}</span>,
}));

// Mock LocaleSelector component
vi.mock('./UiLocaleSelector', () => ({
  default: () => <div data-testid="locale-selector">Locale Selector</div>,
}));

// Mock useT hook
vi.mock('../hooks/useT', () => ({
  useT: (key: string) => key,
}));

describe('Login Component', () => {
  const mockLogin = vi.fn();

  const renderLogin = () => {
    const authContextValue = {
      token: null,
      user: null,
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      setToken: vi.fn(),
    };

    return render(
      <BrowserRouter>
        <AuthContext.Provider value={authContextValue}>
          <Login />
        </AuthContext.Provider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('renders login form elements', () => {
    renderLogin();

    // Check title
    expect(screen.getByTestId('ui-label-login.login')).toBeInTheDocument();

    // Check email input
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();

    // Check password input
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

    // Check login button
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();

    // Check forgot password link
    expect(screen.getByRole('link', { name: /forgot.*password/i })).toBeInTheDocument();

    // Check locale selector
    expect(screen.getByTestId('locale-selector')).toBeInTheDocument();
  });

  it('submits login form with credentials', async () => {
    mockLogin.mockResolvedValue(undefined);

    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Fill in credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'SecurePass123!' } });

    // Submit form
    fireEvent.click(loginButton);

    // Wait for login to be called
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'SecurePass123!');
    });
  });

  it('displays error message on login failure', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid email or password'));

    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Fill in credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

    // Submit form
    fireEvent.click(loginButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
    });

    // Error should be in a red error box
    const errorDiv = screen.getByText('Invalid email or password').closest('div');
    expect(errorDiv).toHaveClass('bg-red-100', 'border-red-400', 'text-red-700');
  });

  it('clears error message when user starts typing', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid email or password'));

    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Submit with wrong credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrong' } });
    fireEvent.click(loginButton);

    // Wait for error
    await waitFor(() => {
      expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
    });

    // Start typing in email field
    fireEvent.change(emailInput, { target: { value: 'test@example.com!' } });

    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Invalid email or password')).not.toBeInTheDocument();
    });
  });

  it('shows loading state during login', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    mockLogin.mockReturnValue(promise);

    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Fill in and submit
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password' } });
    fireEvent.click(loginButton);

    // Button should be disabled and show loading text
    await waitFor(() => {
      expect(loginButton).toBeDisabled();
      expect(screen.getByText('Logging in...')).toBeInTheDocument();
    });

    // Resolve the promise
    resolvePromise!(undefined);

    // Wait for loading to finish
    await waitFor(() => {
      expect(loginButton).not.toBeDisabled();
    });
  });

  it('displays generic error message when no specific error provided', async () => {
    mockLogin.mockRejectedValue({});

    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password' } });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText(/login failed.*check your credentials/i)).toBeInTheDocument();
    });
  });

  it('has proper form attributes for accessibility', () => {
    renderLogin();

    const emailInput = screen.getByRole('textbox', { name: /email/i }) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;

    // Email input
    expect(emailInput.type).toBe('text');
    expect(emailInput.name).toBe('email');
    expect(emailInput.autocomplete).toBe('email');

    // Password input
    expect(passwordInput.type).toBe('password');
    expect(passwordInput.name).toBe('password');
    expect(passwordInput.autocomplete).toBe('current-password');
  });

  it('forgot password link navigates to correct URL', () => {
    renderLogin();

    const forgotPasswordLink = screen.getByRole('link', { name: /forgot.*password/i });
    expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
  });
});
