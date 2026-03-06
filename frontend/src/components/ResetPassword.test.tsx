// frontend/src/components/ResetPassword.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ResetPassword from './ResetPassword';
import api from '../api/api';

// Mock the API
vi.mock('../api/api');

// Mock UiLabel component
vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span data-testid={`ui-label-${k}`}>{k}</span>,
}));

// Mock useT hook
vi.mock('../hooks/useT', () => ({
  useT: (key: string) => key,
}));

// Mock useNavigate
const mockNavigate = vi.fn();
let mockToken: string | null = 'test-token-123';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams(mockToken ? `token=${mockToken}` : '')],
  };
});

describe('ResetPassword Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockToken = 'test-token-123';
  });

  it('renders the reset password form when token is present', () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    // Check title
    expect(screen.getByTestId('ui-label-reset_password.title.reset_password')).toBeInTheDocument();

    // Check password inputs
    const passwordInputs = screen.getAllByLabelText(/password/i);
    expect(passwordInputs).toHaveLength(2);

    // Check submit button
    expect(screen.getByRole('button', { name: 'reset_password.button.reset_password' })).toBeInTheDocument();

    // Check back to login link
    expect(screen.getByRole('link', { name: 'reset_password.link.back_to_login' })).toBeInTheDocument();
  });

  it('shows invalid token message when token is missing', () => {
    mockToken = null;

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    // Should show invalid link message
    expect(screen.getByTestId('ui-label-reset_password.title.invalid_link')).toBeInTheDocument();
    expect(screen.getByTestId('ui-label-reset_password.message.link_invalid_or_expired')).toBeInTheDocument();
  });

  it('submits form with valid matching passwords', async () => {
    const mockPost = vi.mocked(api.post).mockResolvedValue({ data: {} });

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const [passwordInput, confirmPasswordInput] = screen.getAllByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: 'reset_password.button.reset_password' });

    // Fill in passwords
    fireEvent.change(passwordInput, { target: { value: 'NewSecure@Pass123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'NewSecure@Pass123' } });

    // Submit form
    fireEvent.click(submitButton);

    // Wait for API call
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/auth/reset-password', {
        token: 'test-token-123',
        new_password: 'NewSecure@Pass123',
      });
    });

    // Should navigate to login
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login?reset=success');
    });
  });

  it('shows error when passwords do not match', async () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const [passwordInput, confirmPasswordInput] = screen.getAllByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: 'reset_password.button.reset_password' });

    // Fill in non-matching passwords
    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPass123!' } });

    // Submit form
    fireEvent.click(submitButton);

    // Should show error
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });

    // Should not call API
    expect(api.post).not.toHaveBeenCalled();
  });

  it('shows error message on API failure', async () => {
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Invalid or expired token' } },
    });

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const [passwordInput, confirmPasswordInput] = screen.getAllByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: 'reset_password.button.reset_password' });

    fireEvent.change(passwordInput, { target: { value: 'NewSecure@Pass123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'NewSecure@Pass123' } });
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Invalid or expired token')).toBeInTheDocument();
    });
  });

  it('shows password validation errors from backend', async () => {
    vi.mocked(api.post).mockRejectedValue({
      response: {
        data: {
          detail: {
            message: 'Password does not meet security requirements',
            errors: ['Must contain uppercase', 'Must contain special character'],
          },
        },
      },
    });

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const [passwordInput, confirmPasswordInput] = screen.getAllByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: 'reset_password.button.reset_password' });

    fireEvent.change(passwordInput, { target: { value: 'weakpass' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'weakpass' } });
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/password does not meet security requirements/i)).toBeInTheDocument();
      expect(screen.getByText(/must contain uppercase.*must contain special character/i)).toBeInTheDocument();
    });
  });

  it('disables button and shows loading state during submission', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    vi.mocked(api.post).mockReturnValue(promise as any);

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const [passwordInput, confirmPasswordInput] = screen.getAllByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: 'reset_password.button.reset_password' });

    fireEvent.change(passwordInput, { target: { value: 'NewSecure@Pass123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'NewSecure@Pass123' } });
    fireEvent.click(submitButton);

    // Button should be disabled during submission
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByTestId('ui-label-reset_password.button.resetting')).toBeInTheDocument();
    });

    // Resolve the promise and wait for React to process the async state update.
    await act(async () => {
      resolvePromise!({ data: {} });
      await promise;
    });
  });

  it('requires both password fields to be filled', () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordInputs = screen.getAllByLabelText(/password/i) as HTMLInputElement[];

    passwordInputs.forEach((input) => {
      expect(input.required).toBe(true);
      expect(input.type).toBe('password');
      expect(input.minLength).toBe(8);
    });
  });
});
