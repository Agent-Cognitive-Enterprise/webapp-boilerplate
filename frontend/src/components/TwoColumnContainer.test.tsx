import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TwoColumnContainer from './TwoColumnContainer';
import { getUserSettings, setUserSettings } from '../api/userSettings';

vi.mock('../api/userSettings', () => ({
  getUserSettings: vi.fn(),
  setUserSettings: vi.fn(),
}));

vi.mock('../hooks/useDebounce', () => ({
  useDebounce: (fn: (...args: any[]) => void) => fn,
}));

describe('TwoColumnContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getUserSettings).mockResolvedValue({ settings: { columnWidths: [70, 30] } } as any);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      width: 1000,
      height: 500,
      top: 0,
      left: 0,
      right: 1000,
      bottom: 500,
      toJSON: () => ({}),
    } as DOMRect);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads saved widths and renders columns', async () => {
    render(
      <TwoColumnContainer
        left={<div>Left</div>}
        right={<div>Right</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalledWith('/page/two-column-widths');
    });
    expect(screen.getAllByText('Left').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Right').length).toBeGreaterThan(0);
  });

  it('updates and saves widths while dragging separator', async () => {
    render(
      <TwoColumnContainer
        left={<div>Left</div>}
        right={<div>Right</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalled();
    });

    const separator = screen.getByRole('separator', { name: 'Resize Column 1 and 2' });
    fireEvent.mouseDown(separator, { clientX: 100 });
    fireEvent.mouseMove(window, { clientX: 180 });
    fireEvent.mouseUp(window);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/two-column-widths',
        { columnWidths: expect.any(Array) }
      );
    });
  });
});
