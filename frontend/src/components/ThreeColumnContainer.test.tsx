import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ThreeColumnContainer from './ThreeColumnContainer';
import { getUserSettings, setUserSettings } from '../api/userSettings';

vi.mock('../api/userSettings', () => ({
  getUserSettings: vi.fn(),
  setUserSettings: vi.fn(),
}));

vi.mock('../hooks/useDebounce', () => ({
  useDebounce: (fn: (...args: any[]) => void) => fn,
}));

describe('ThreeColumnContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getUserSettings).mockResolvedValue({ settings: { columnWidths: [30, 50, 20] } } as any);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      width: 1000,
      height: 600,
      top: 0,
      left: 0,
      right: 1000,
      bottom: 600,
      toJSON: () => ({}),
    } as DOMRect);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads saved widths and renders all column content', async () => {
    render(
      <ThreeColumnContainer
        left={<div>Left</div>}
        center={<div>Center</div>}
        right={<div>Right</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalledWith('/page/three-column-widths');
    });
    expect(screen.getAllByText('Left').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Center').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Right').length).toBeGreaterThan(0);
  });

  it('saves width updates when dragging second separator', async () => {
    render(
      <ThreeColumnContainer
        left={<div>Left</div>}
        center={<div>Center</div>}
        right={<div>Right</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalled();
    });

    const separator = screen.getByRole('separator', { name: 'Resize Column 2 and 3' });
    fireEvent.mouseDown(separator, { clientX: 400 });
    fireEvent.mouseMove(window, { clientX: 460 });
    fireEvent.mouseUp(window);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/three-column-widths',
        { columnWidths: expect.any(Array) }
      );
    });
  });
});
