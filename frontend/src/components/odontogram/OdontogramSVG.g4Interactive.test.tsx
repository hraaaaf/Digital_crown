import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OdontogramSVG } from './OdontogramSVG';

class ResizeObserverMock {
  private readonly callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(target: Element) {
    this.callback([{ target } as ResizeObserverEntry], this as unknown as ResizeObserver);
  }

  unobserve() {}
  disconnect() {}
}

describe('OdontogramSVG G4 accessible interaction contract', () => {
  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 480,
      height: 320,
      top: 0,
      left: 0,
      right: 480,
      bottom: 320,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    } as DOMRect);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('exposes an interactive tooth as an accessible button and activates its occlusal surface', async () => {
    const onSurfaceClick = vi.fn();

    render(
      <OdontogramSVG
        type="ADULT"
        teethSurfaces={{}}
        selectedTooth={null}
        selectedSurface={null}
        onSurfaceClick={onSurfaceClick}
        readOnly={false}
      />,
    );

    const tooth11 = await screen.findByRole('button', { name: /^Dent 11,/ });
    fireEvent.click(tooth11);

    expect(onSurfaceClick).toHaveBeenCalledWith(11, 'O', expect.anything());

    onSurfaceClick.mockClear();
    fireEvent.keyDown(tooth11, { key: 'Enter' });
    expect(onSurfaceClick).toHaveBeenCalledWith(11, 'O', expect.anything());
  });

  it('does not expose tooth buttons in read-only mode', () => {
    render(
      <OdontogramSVG
        type="ADULT"
        teethSurfaces={{}}
        selectedTooth={null}
        selectedSurface={null}
        onSurfaceClick={vi.fn()}
        readOnly
      />,
    );

    expect(screen.queryByRole('button', { name: /^Dent 11,/ })).toBeNull();
  });
});
