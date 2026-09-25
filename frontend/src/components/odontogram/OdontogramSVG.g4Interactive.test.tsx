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

  it('renders the compact adult FDI renderer with numbers by default', () => {
    render(
      <OdontogramSVG
        type="ADULT"
        teethSurfaces={{}}
        selectedTooth={null}
        selectedSurface={null}
        onSurfaceClick={vi.fn()}
      />,
    );

    expect(document.querySelector('[data-odontogram-renderer="compact-fdi"]')).toBeTruthy();
    expect(screen.getAllByRole('button', { name: /^Dent / })).toHaveLength(32);
    expect(screen.getByText('18')).toBeTruthy();
    expect(screen.getByText('28')).toBeTruthy();
    expect(screen.getByText('48')).toBeTruthy();
    expect(screen.getByText('38')).toBeTruthy();
  });

  it('preserves the pediatric FDI contract with twenty accessible teeth', () => {
    render(
      <OdontogramSVG
        type="PEDIATRIC"
        teethSurfaces={{}}
        selectedTooth={null}
        selectedSurface={null}
        onSurfaceClick={vi.fn()}
      />,
    );

    expect(screen.getAllByRole('button', { name: /^Dent / })).toHaveLength(20);
    expect(screen.getByText('55')).toBeTruthy();
    expect(screen.getByText('65')).toBeTruthy();
    expect(screen.getByText('85')).toBeTruthy();
    expect(screen.getByText('75')).toBeTruthy();
  });

  it('exposes the selected tooth state through aria and the primary halo', () => {
    render(
      <OdontogramSVG
        type="ADULT"
        teethSurfaces={{}}
        selectedTooth={16}
        selectedSurface="O"
        onSurfaceClick={vi.fn()}
      />,
    );

    const tooth16 = screen.getByRole('button', { name: /^Dent 16,/ });
    expect(tooth16).toHaveAttribute('aria-pressed', 'true');
    expect(tooth16.querySelector('rect[stroke="var(--primary)"]')).toBeTruthy();
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
