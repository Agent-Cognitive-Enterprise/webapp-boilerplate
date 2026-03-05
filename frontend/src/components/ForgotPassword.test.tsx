// frontend/src/components/ForgotPassword.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ForgotPassword from './ForgotPassword';
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

describe('ForgotPassword Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the forgot password form', () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    // Check title
    expect(screen.getByTestId('ui-label-forgot_password.title.forgot_password')).toBeInTheDocument();

    // Redundant helper text is intentionally omitted to avoid duplicate email prompts.
    expect(screen.queryByTestId('ui-label-forgot_password.message.enter_email')).not.toBeInTheDocument();

    // Check email input
    const emailInput = screen.getByRole('textbox', { name: 'forgot_password.label.email' });
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).not.toHaveAttribute('placeholder');

    // Check submit button
    expect(screen.getByRole('button')).toBeInTheDocument();

    // Check back to login link
    expect(screen.getByTestId('ui-label-forgot_password.link.back_to_login')).toBeInTheDocument();
  });

  it('submits the form with valid email', async () => {
    const mockPost = vi.mocked(api.post).mockResolvedValue({ data: {} });

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: 'forgot_password.label.email' });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    // Fill in email
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    // Submit form
    fireEvent.click(submitButton);

    // Wait for API call
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/auth/forgot-password', {
        email: 'test@example.com',
      });
    });
  });

  it('shows success message after successful submission', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} });

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: 'forgot_password.label.email' });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByTestId('ui-label-forgot_password.title.check_email')).toBeInTheDocument();
      expect(screen.getByTestId('ui-label-forgot_password.message.instructions_sent')).toBeInTheDocument();
    });
  });

  it('shows generic error message on API failure without leaking backend details', async () => {
    const mockPost = vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Server error' } },
    });

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Failed to send reset email. Please try again.')).toBeInTheDocument();
    });
    expect(screen.queryByText('Server error')).not.toBeInTheDocument();

    expect(mockPost).toHaveBeenCalledTimes(1);
  });

  it('shows generic error message when no detail provided', async () => {
    vi.mocked(api.post).mockRejectedValue({});

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to send reset email/i)).toBeInTheDocument();
    });
  });

  it('treats 404 as generic success to prevent account enumeration', async () => {
    vi.mocked(api.post).mockRejectedValue({
      response: { status: 404, data: { detail: 'Not Found' } },
    });

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    fireEvent.change(emailInput, { target: { value: 'unknown@example.com' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByTestId('ui-label-forgot_password.title.check_email')).toBeInTheDocument();
      expect(screen.getByTestId('ui-label-forgot_password.message.instructions_sent')).toBeInTheDocument();
    });
    expect(screen.queryByText('Not Found')).not.toBeInTheDocument();
  });

  it('disables button and shows loading state during submission', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    vi.mocked(api.post).mockReturnValue(promise as any);

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const submitButton = screen.getByRole('button', { name: 'forgot_password.button.send_reset_link' });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    // Button should be disabled during submission
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByTestId('ui-label-forgot_password.button.sending')).toBeInTheDocument();
    });

    // Resolve the promise
    resolvePromise!({ data: {} });

    // Wait for success state
    await waitFor(() => {
      expect(screen.getByTestId('ui-label-forgot_password.title.check_email')).toBeInTheDocument();
    });
  });

  it('requires email input to be filled', () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByRole('textbox', { name: /email/i }) as HTMLInputElement;

    expect(emailInput.required).toBe(true);
    expect(emailInput.type).toBe('email');
  });
});
