import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ThreeRowContainer from './ThreeRowContainer';
import { getUserSettings, setUserSettings } from '../api/userSettings';

vi.mock('../api/userSettings', () => ({
  getUserSettings: vi.fn(),
  setUserSettings: vi.fn(),
}));

vi.mock('../hooks/useDebounce', () => ({
  useDebounce: (fn: (...args: any[]) => void) => fn,
}));

describe('ThreeRowContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getUserSettings).mockResolvedValue({ settings: { rowHeights: [30, 40, 30] } } as any);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      width: 900,
      height: 600,
      top: 0,
      left: 0,
      right: 900,
      bottom: 600,
      toJSON: () => ({}),
    } as DOMRect);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads saved heights and renders all row content', async () => {
    render(
      <ThreeRowContainer
        top={<div>Top</div>}
        center={<div>Center</div>}
        bottom={<div>Bottom</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalledWith('/page/three-row-heights');
    });
    expect(screen.getAllByText('Top').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Center').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Bottom').length).toBeGreaterThan(0);
  });

  it('saves heights while dragging first separator', async () => {
    render(
      <ThreeRowContainer
        top={<div>Top</div>}
        center={<div>Center</div>}
        bottom={<div>Bottom</div>}
        parentUrl="/page"
      />
    );

    const separator = screen.getByRole('separator', { name: 'Resize Row 1 and 2' });
    fireEvent.mouseDown(separator, { clientY: 120 });
    fireEvent.mouseMove(window, { clientY: 180 });
    fireEvent.mouseUp(window);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/three-row-heights',
        { rowHeights: expect.any(Array) }
      );
    });
  });

  it('resets heights on double click and persists defaults', async () => {
    render(
      <ThreeRowContainer
        top={<div>Top</div>}
        center={<div>Center</div>}
        bottom={<div>Bottom</div>}
        parentUrl="/page"
      />
    );

    const separator = screen.getByRole('separator', { name: 'Resize Row 2 and 3' });
    fireEvent.doubleClick(separator);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/three-row-heights',
        { rowHeights: [33.3, 33.3, 33.4] }
      );
    });
  });
});
