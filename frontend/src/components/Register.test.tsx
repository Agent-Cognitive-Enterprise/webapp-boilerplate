import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Register from './Register';
import { AuthContext } from '../contexts/AuthContext';

vi.mock('./UiLabel', () => ({
  default: ({ k }: { k: string }) => <span data-testid={`ui-label-${k}`}>{k}</span>,
}));

vi.mock('./UiLocaleSelector', () => ({
  default: () => <div data-testid="locale-selector">Locale Selector</div>,
}));

vi.mock('../hooks/useT', () => ({
  useT: (key: string) => key,
}));

describe('Register Component', () => {
  const mockRegister = vi.fn();

  function renderRegister() {
    const authValue = {
      token: null,
      user: null,
      login: vi.fn(),
      register: mockRegister,
      logout: vi.fn(),
      setToken: vi.fn(),
    };

    return render(
      <BrowserRouter>
        <AuthContext.Provider value={authValue}>
          <Register />
        </AuthContext.Provider>
      </BrowserRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders required registration fields and locale selector', () => {
    renderRegister();

    expect(screen.getByTestId('ui-label-register.title.register')).toBeInTheDocument();
    expect(screen.getByTestId('locale-selector')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /full_name/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  it('submits form values to auth context register()', async () => {
    renderRegister();

    fireEvent.change(screen.getByRole('textbox', { name: /full_name/i }), {
      target: { value: 'Test User' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /email/i }), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'SecurePass123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('Test User', 'test@example.com', 'SecurePass123!');
    });
  });
});

