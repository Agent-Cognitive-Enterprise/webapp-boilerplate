import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TranslationModal } from './TranslationModal';
import { AuthContext } from '../../contexts/AuthContext';
import { useUiLabelContext } from '../../contexts/UiLabelProvider';
import { useUiLabel } from '../../hooks/useUiLabel';

vi.mock('../../contexts/UiLabelProvider.tsx', () => ({
  useUiLabelContext: vi.fn(),
}));

vi.mock('../../hooks/useUiLabel.ts', () => ({
  useUiLabel: vi.fn(),
}));

vi.mock('../UiLabel.tsx', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

function renderModal(token: string | null, onClose = vi.fn()) {
  const authValue = {
    token,
    user: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    setToken: vi.fn(),
  };

  return render(
    <AuthContext.Provider value={authValue}>
      <TranslationModal
        keyName="profile.label.full_name"
        locale="fr"
        englishValue="Full Name"
        currentValue="Nom Complet"
        onClose={onClose}
      />
    </AuthContext.Provider>
  );
}

describe('TranslationModal', () => {
  const suggest = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useUiLabelContext).mockReturnValue({
      suggest,
      request: vi.fn(),
      getValue: vi.fn(),
      subscribe: vi.fn(),
    } as any);

    vi.mocked(useUiLabel).mockImplementation((key: string, locale: string) => {
      if (locale === 'en') return { value: `EN:${key}` } as any;
      return { value: `FR:${key}` } as any;
    });
  });

  it('does not render without auth token', () => {
    const { container } = renderModal(null);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders key tail and current values when authenticated', () => {
    renderModal('token-123');
    expect(screen.getByText('full_name')).toBeInTheDocument();
    expect(screen.getByText('EN:profile.label.full_name')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Nom Complet')).toBeInTheDocument();
  });

  it('submits suggestion and closes modal', () => {
    const onClose = vi.fn();
    renderModal('token-123', onClose);

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Nom modifie' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'button.submit' }));

    expect(suggest).toHaveBeenCalledWith('profile.label.full_name', 'fr', 'Nom modifie');
    expect(onClose).toHaveBeenCalled();
  });
});
