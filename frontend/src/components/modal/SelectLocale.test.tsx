import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SelectLocaleModal from './SelectLocale';

vi.mock('../UiLabel.tsx', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

describe('SelectLocaleModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading state', () => {
    render(
      <SelectLocaleModal
        locales={[]}
        loading
        selected="en"
        onClose={vi.fn()}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('common.loading')).toBeInTheDocument();
  });

  it('selects locale and saves selection', () => {
    const onClose = vi.fn();
    const onSelect = vi.fn();

    render(
      <SelectLocaleModal
        locales={['en', 'fr']}
        loading={false}
        selected="en"
        onClose={onClose}
        onSelect={onSelect}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /français/i }));
    fireEvent.click(screen.getByRole('button', { name: 'button.save' }));

    expect(onSelect).toHaveBeenCalledWith('fr');
    expect(onClose).toHaveBeenCalled();
  });
});
