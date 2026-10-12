import { useState } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Landmark } from '../cephaloShared';
import { CephaloLandmarkReticles } from './CephaloLandmarkReticles';
import { CephaloTracingLayer as CephaloTracingLayerBase } from '../CephaloTracingLayerBase';

const baseline: Landmark[] = [{ id: 'N', x: 30, y: 40 }, { id: 'S', x: 60, y: 70 }];

const palette = {
  ptU: '#123456',
  ptL: '#123456',
  ptDefault: '#abcdef',
  ptSoft: '#abcdef',
  ptFocus: '#ffffff',
  text: '#ffffff',
  magnifierBg: '#000000',
  isolationDim: 0.08,
};

const clientToSVG = (x: number, y: number) => ({ x, y });

function Fixture({ onUpdate }: { onUpdate: (pts: Landmark[]) => void }) {
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [activeDragPos, setActiveDragPos] = useState<{ id: string; x: number; y: number } | null>(null);
  const [, setMagnifier] = useState({ x: 0, y: 0, show: false });
  return (
    <svg>
      <g data-testid="drag-state" data-active={activeDragId ?? ''} data-preview={activeDragPos?.id ?? ''} />
      <CephaloLandmarkReticles
        landmarks={baseline}
        isCalibrating={false}
        baseOpacity={1}
        activeDragId={activeDragId}
        activeDragPos={activeDragPos}
        palette={palette}
        isPro={false}
        setActiveDragId={setActiveDragId}
        setActiveDragPos={setActiveDragPos}
        magnifierEnabled={true}
        setMagnifier={setMagnifier}
        clientToSVG={clientToSVG}
        onUpdateLandmarks={onUpdate}
      />
    </svg>
  );
}

const dragHandle = () => document.querySelector('[data-ceph03b-drag-handle="N"]') as SVGGElement;
const state = () => screen.getByTestId('drag-state');

// JSDOM does not populate PointerEvent.clientX/clientY with fireEvent.pointer*.
// Dispatch a DOM pointer event with real MouseEvent coordinates so the commit
// assertion exercises a meaningful, finite coordinate oracle.
const dispatchPointer = (
  handle: Element, type: string, pointerId: number, clientX = 0, clientY = 0,
) => {
  const event = new MouseEvent(type, { bubbles: true, clientX, clientY });
  Object.defineProperty(event, 'pointerId', { value: pointerId });
  fireEvent(handle, event);
};

describe('DC-CEPH03B desktop landmark drag lifecycle', () => {
  const originalSvgPoint = SVGSVGElement.prototype.createSVGPoint;
  const originalScreenCTM = SVGSVGElement.prototype.getScreenCTM;
  const originalCapture = Element.prototype.setPointerCapture;
  beforeEach(() => {
    Object.defineProperty(Element.prototype, 'setPointerCapture', {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
  });

  afterEach(() => {
    cleanup();
    if (originalCapture) {
      Object.defineProperty(Element.prototype, 'setPointerCapture', {
        configurable: true, writable: true, value: originalCapture,
      });
    } else {
      delete (Element.prototype as Element & { setPointerCapture?: unknown }).setPointerCapture;
    }
    for (const [name, original] of [
      ['createSVGPoint', originalSvgPoint],
      ['getScreenCTM', originalScreenCTM],
    ] as const) {
      if (original) Object.defineProperty(SVGSVGElement.prototype, name, {
        configurable: true, writable: true, value: original,
      });
      else delete (SVGSVGElement.prototype as unknown as Record<string, unknown>)[name];
    }
    vi.restoreAllMocks();
  });

  it('cancels a pointer gesture without an audited/persisted edit', () => {
    const onUpdate = vi.fn();
    render(<Fixture onUpdate={onUpdate} />);
    const handle = dragHandle();
    dispatchPointer(handle, 'pointerdown', 5, 30, 40);
    dispatchPointer(handle, 'pointermove', 5, 90, 100);
    expect(state().getAttribute('data-active')).toBe('N');
    expect(state().getAttribute('data-preview')).toBe('N');
    dispatchPointer(handle, 'pointercancel', 5);
    expect(state().getAttribute('data-active')).toBe('');
    expect(state().getAttribute('data-preview')).toBe('');
    expect(onUpdate).not.toHaveBeenCalled();
  });

  it('clears a lost pointer capture without persisting a partial gesture', () => {
    const onUpdate = vi.fn();
    render(<Fixture onUpdate={onUpdate} />);
    const handle = dragHandle();
    dispatchPointer(handle, 'pointerdown', 6, 30, 40);
    dispatchPointer(handle, 'pointermove', 6, 100, 120);
    fireEvent(handle, new Event('lostpointercapture', { bubbles: true }));
    expect(state().getAttribute('data-active')).toBe('');
    expect(state().getAttribute('data-preview')).toBe('');
    expect(onUpdate).not.toHaveBeenCalled();
  });

  it('commits only the selected landmark on a completed pointer-up', () => {
    const onUpdate = vi.fn();
    render(<Fixture onUpdate={onUpdate} />);
    const handle = dragHandle();
    dispatchPointer(handle, 'pointerdown', 7, 30, 40);
    dispatchPointer(handle, 'pointermove', 7, 75, 82);
    dispatchPointer(handle, 'pointerup', 7, 75, 82);
    expect(onUpdate).toHaveBeenCalledTimes(1);
    expect(onUpdate).toHaveBeenCalledWith([
      { id: 'N', x: 75, y: 82 },
      { id: 'S', x: 60, y: 70 },
    ]);
    expect(state().getAttribute('data-active')).toBe('');
    expect(state().getAttribute('data-preview')).toBe('');
  });

  it('renders an anatomical SN trace at the live preview position under enabled VTO, then restores it on cancel', () => {
    // Identity CTM: the oracle does not depend on viewBox pixel scaling.
    Object.defineProperty(SVGSVGElement.prototype, 'getScreenCTM', {
      configurable: true, value: () => ({ inverse: () => ({}) }),
    });
    Object.defineProperty(SVGSVGElement.prototype, 'createSVGPoint', {
      configurable: true, value: () => ({
        x: 0, y: 0,
        matrixTransform(this: { x: number; y: number }) {
          return { x: this.x, y: this.y };
        },
      }),
    });

    const onUpdate = vi.fn();
    render(
      <CephaloTracingLayerBase
        landmarks={[{ id: 'S', x: 30, y: 40 }, { id: 'N', x: 60, y: 50 }]}
        imageWidth={300}
        imageHeight={300}
        onUpdateLandmarks={onUpdate}
        magnifierEnabled={false}
        activeAnalysis="steiner"
        vto={{ enabled: true, showGhostFace: false, showSoftTissue: false }}
      />,
    );

    const line = () => document.querySelector('[data-cephalo-line-key="sn"]');
    expect(line()).not.toBeNull();
    expect(line()?.getAttribute('x2')).toBe('60');
    const handle = dragHandle();
    dispatchPointer(handle, 'pointerdown', 8, 60, 50);
    dispatchPointer(handle, 'pointermove', 8, 110, 95);
    expect(line()?.getAttribute('x2')).toBe('110');
    expect(line()?.getAttribute('y2')).toBe('95');
    expect(onUpdate).not.toHaveBeenCalled();
    dispatchPointer(handle, 'pointercancel', 8);
    expect(line()?.getAttribute('x2')).toBe('60');
    expect(line()?.getAttribute('y2')).toBe('50');
    expect(onUpdate).not.toHaveBeenCalled();
  });

});
