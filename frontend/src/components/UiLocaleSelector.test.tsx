import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UiLocaleSelector from './UiLocaleSelector';
import api from '../api/api';

vi.mock('../api/api');

vi.mock('./modal/SelectLocale.tsx', () => ({
  default: (props: any) => (
    <div data-testid="locale-modal">
      <div data-testid="modal-selected">{props.selected}</div>
      <div data-testid="modal-loading">{String(props.loading)}</div>
      <div data-testid="modal-locales">{props.locales.join(',')}</div>
      <button onClick={() => props.onSelect('fr')}>Select French</button>
      <button onClick={props.onClose}>Close</button>
    </div>
  ),
}));

describe('UiLocaleSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads locales and opens modal with fetched data', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { data: ['en', 'fr'] } } as any);
    localStorage.setItem('uiLocale', 'en');

    render(<UiLocaleSelector />);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/ui-label',
        { action: 'list' },
        expect.objectContaining({ headers: expect.any(Object) })
      );
    });

    fireEvent.click(screen.getByText('English'));
    expect(screen.getByTestId('locale-modal')).toBeInTheDocument();
    expect(screen.getByTestId('modal-selected')).toHaveTextContent('en');
    expect(screen.getByTestId('modal-loading')).toHaveTextContent('false');
    expect(screen.getByTestId('modal-locales')).toHaveTextContent('en,fr');
  });

  it('stores selected locale and reloads page', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { data: ['en', 'fr'] } } as any);

    render(<UiLocaleSelector />);

    fireEvent.click(screen.getByText('English'));
    fireEvent.click(screen.getByRole('button', { name: 'Select French' }));

    expect(localStorage.getItem('uiLocale')).toBe('fr');
  });

  it('handles list API failure gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(api.post).mockRejectedValue(new Error('network error'));

    render(<UiLocaleSelector />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });
    expect(screen.getByText('English')).toBeInTheDocument();
  });
});
