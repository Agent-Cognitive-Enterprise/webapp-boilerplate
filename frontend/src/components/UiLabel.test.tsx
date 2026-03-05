import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import UiLabel from './UiLabel';
import { useUiLabel } from '../hooks/useUiLabel';
import { useUiLabelContext } from '../contexts/UiLabelProvider';

vi.mock('../hooks/useUiLabel.ts', () => ({
  useUiLabel: vi.fn(),
}));

vi.mock('../contexts/UiLabelProvider.tsx', () => ({
  useUiLabelContext: vi.fn(),
}));

vi.mock('./modal/TranslationModal', () => ({
  TranslationModal: (props: any) => <div data-testid="translation-modal">{props.keyName}</div>,
}));

describe('UiLabel Component', () => {
  const request = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('uiLocale', 'fr');
    vi.mocked(useUiLabelContext).mockReturnValue({
      request,
      suggest: vi.fn(),
      getValue: vi.fn(),
      subscribe: vi.fn(),
    } as any);
  });

  it('renders target locale value and applies fillers', () => {
    vi.mocked(useUiLabel).mockImplementation((_k: string, locale: string) => {
      if (locale === 'fr') return { value: 'Bonjour %name%' } as any;
      return { value: 'Hello %name%' } as any;
    });

    render(<UiLabel k="greeting.message" fillers={{ name: 'Alice' }} />);
    expect(screen.getByText('Bonjour Alice')).toBeInTheDocument();
  });

  it('falls back to english when locale value is missing', () => {
    vi.mocked(useUiLabel).mockImplementation((_k: string, locale: string) => {
      if (locale === 'fr') return { value: undefined } as any;
      return { value: 'Hello' } as any;
    });

    render(<UiLabel k="greeting.message" />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders blurred key tail when no translation is available', () => {
    vi.mocked(useUiLabel).mockReturnValue({ value: undefined } as any);
    render(<UiLabel k="reset_password.button.submit" />);

    const tail = screen.getByText('submit');
    expect(tail).toBeInTheDocument();
    expect(tail.className).toContain('blur-[2px]');
  });

  it('supports custom html tag via "as" prop', () => {
    vi.mocked(useUiLabel).mockImplementation((_k: string, locale: string) => {
      if (locale === 'fr') return { value: 'Titre' } as any;
      return { value: 'Title' } as any;
    });

    render(<UiLabel k="page.title" as="h3" />);
    const h3 = screen.getByText('Titre');
    expect(h3.tagName).toBe('H3');
  });

  it('opens translation modal on right click and requests english key', () => {
    vi.mocked(useUiLabel).mockImplementation((_k: string, locale: string) => {
      if (locale === 'fr') return { value: 'Bonjour' } as any;
      return { value: 'Hello' } as any;
    });

    render(<UiLabel k="hello.world" />);
    const label = screen.getByText('Bonjour');
    fireEvent.contextMenu(label);

    expect(request).toHaveBeenCalledWith('hello.world', 'en');
    expect(screen.getByTestId('translation-modal')).toBeInTheDocument();
  });
});

