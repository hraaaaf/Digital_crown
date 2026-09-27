import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OdontogramSVG } from './OdontogramSVG';

const ADULT = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,31,32,33,34,35,36,37,38,41,42,43,44,45,46,47,48];
const CHILD = [55,54,53,52,51,61,62,63,64,65,71,72,73,74,75,81,82,83,84,85];

class ResizeObserverMock {
  private readonly callback: ResizeObserverCallback;
  constructor(callback: ResizeObserverCallback) { this.callback = callback; }
  observe(target: Element) { this.callback([{ target } as ResizeObserverEntry], this as unknown as ResizeObserver); }
  unobserve() {}
  disconnect() {}
}

describe('OdontogramSVG G4 accessible interaction contract', () => {
  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 480, height: 360, top: 0, left: 0, right: 480, bottom: 360, x: 0, y: 0, toJSON: () => ({}),
    } as DOMRect);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('maps every adult FDI tooth to the correct clinical button', () => {
    const onSurfaceClick = vi.fn();
    render(<OdontogramSVG type="ADULT" teethSurfaces={{}} selectedTooth={null} selectedSurface={null} onSurfaceClick={onSurfaceClick} readOnly={false} />);

    expect(screen.getAllByRole('button')).toHaveLength(32);
    ADULT.forEach((tooth) => fireEvent.click(screen.getByRole('button', { name: new RegExp(`^Dent ${tooth}(?:,|$)`) })));
    expect(onSurfaceClick.mock.calls.map(([tooth, surface]) => [tooth, surface])).toEqual(ADULT.map((tooth) => [tooth, 'O']));
  });

  it('maps every primary FDI tooth to the correct clinical button', () => {
    const onSurfaceClick = vi.fn();
    render(<OdontogramSVG type="PEDIATRIC" teethSurfaces={{}} selectedTooth={null} selectedSurface={null} onSurfaceClick={onSurfaceClick} readOnly={false} />);

    expect(screen.getAllByRole('button')).toHaveLength(20);
    CHILD.forEach((tooth) => fireEvent.click(screen.getByRole('button', { name: new RegExp(`^Dent ${tooth}(?:,|$)`) })));
    expect(onSurfaceClick.mock.calls.map(([tooth, surface]) => [tooth, surface])).toEqual(CHILD.map((tooth) => [tooth, 'O']));
  });

  it('keeps keyboard activation on the selected clinical tooth', () => {
    const onSurfaceClick = vi.fn();
    render(<OdontogramSVG type="ADULT" teethSurfaces={{}} selectedTooth={null} selectedSurface={null} onSurfaceClick={onSurfaceClick} readOnly={false} />);
    const tooth11 = screen.getByRole('button', { name: /^Dent 11(?:,|$)/ });
    fireEvent.keyDown(tooth11, { key: 'Enter' });
    expect(onSurfaceClick).toHaveBeenCalledWith(11, 'O', expect.anything());
  });

  it('does not expose tooth buttons in read-only mode', () => {
    render(<OdontogramSVG type="ADULT" teethSurfaces={{}} selectedTooth={null} selectedSurface={null} onSurfaceClick={vi.fn()} readOnly />);
    expect(screen.queryByRole('button', { name: /^Dent 11(?:,|$)/ })).toBeNull();
  });
});
