import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TwoRowContainer from './TwoRowContainer';
import { getUserSettings, setUserSettings } from '../api/userSettings';

vi.mock('../api/userSettings', () => ({
  getUserSettings: vi.fn(),
  setUserSettings: vi.fn(),
}));

class ResizeObserverMock {
  private readonly cb: ResizeObserverCallback;

  constructor(cb: ResizeObserverCallback) {
    this.cb = cb;
  }

  observe() {
    this.cb([], this as unknown as ResizeObserver);
  }

  disconnect() {}

  unobserve() {}
}

describe('TwoRowContainer', () => {
  beforeAll(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);
    Object.defineProperty(HTMLElement.prototype, 'setPointerCapture', {
      value: vi.fn(),
      configurable: true,
    });
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getUserSettings).mockResolvedValue({ settings: { twoRowSplit: 0.6 } } as any);
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

  it('loads saved split and renders top/down content', async () => {
    render(
      <TwoRowContainer
        top={<div>Top Section</div>}
        down={<div>Bottom Section</div>}
        parentUrl="/page"
      />
    );

    await waitFor(() => {
      expect(getUserSettings).toHaveBeenCalledWith('/page/two-row-split');
    });
    expect(screen.getAllByText('Top Section').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Bottom Section').length).toBeGreaterThan(0);
  });

  it('persists ratio after pointer drag', async () => {
    render(
      <TwoRowContainer
        top={<div>Top Section</div>}
        down={<div>Bottom Section</div>}
        parentUrl="/page"
      />
    );

    const separator = screen.getByRole('separator');

    fireEvent.pointerDown(separator, { pointerId: 1, clientY: 180 });
    fireEvent.pointerMove(window, { clientY: 260 });
    fireEvent.pointerUp(window);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/two-row-split',
        expect.objectContaining({ twoRowSplit: expect.any(Number) })
      );
    });
  });

  it('resets split on double click and saves', async () => {
    render(
      <TwoRowContainer
        top={<div>Top Section</div>}
        down={<div>Bottom Section</div>}
        parentUrl="/page"
      />
    );

    const separator = screen.getByRole('separator');
    fireEvent.doubleClick(separator);

    await waitFor(() => {
      expect(setUserSettings).toHaveBeenCalledWith(
        '/page/two-row-split',
        expect.objectContaining({ twoRowSplit: 0.5 })
      );
    });
  });
});
