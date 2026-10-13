import { useState } from 'react';
import { cleanup, fireEvent, render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import type { Landmark } from './cephaloShared';

const LANDMARKS: Landmark[] = [
  { id: 'Po', x: 30, y: 40 }, { id: 'Or', x: 100, y: 42 },
  { id: 'N', x: 130, y: 70 }, { id: 'Pog', x: 170, y: 175 },
  { id: 'S', x: 75, y: 65 }, { id: 'A', x: 140, y: 100 },
  { id: 'B', x: 155, y: 135 }, { id: 'Go', x: 35, y: 160 },
  { id: 'Me', x: 100, y: 200 },
];
const SYNTHETIC_GHOST = {
  layerId: 't1' as const,
  opacity: 0.5,
  color: '#ffffff',
  landmarks: LANDMARKS.map(p => ({ ...p })),
};

const commit = vi.fn();

function Fixture({ mode }: { mode: 'com' | 'all' }) {
  const [landmarks, setLandmarks] = useState(LANDMARKS.map(p => ({ ...p })));
  return (
    <div style={{ width: 320, height: 320 }}>
      <CephaloTracingLayer
        imageWidth={240}
        imageHeight={240}
        landmarks={landmarks}
        ghosts={[SYNTHETIC_GHOST]}
        onUpdateLandmarks={next => { commit(next); setLandmarks(next); }}
        activeAnalysis={mode}
        magnifierEnabled={false}
        vto={{ enabled: false, showGhostFace: false, showSoftTissue: false, u1_offset: { x: 0, y: 0 }, l1_offset: { x: 0, y: 0 }, mand_offset: { x: 0, y: 0 } }}
      />
    </div>
  );
}

const handle = (id: string) => {
  const element = document.querySelector(`[data-ceph03b-drag-handle="${id}"]`);
  if (!element) throw new Error(`No editable landmark ${id}`);
  return element;
};
const line = (id: string) => {
  const element = document.querySelector(`[data-r19-construction="${id}"],[data-r18-construction="${id}"]`);
  if (!element) throw new Error(`No overlay construction ${id}`);
  return element;
};
const pointer = (element: Element, eventType: string, x = 0, y = 0) => {
  const event = new MouseEvent(eventType, { bubbles: true, clientX: x, clientY: y });
  Object.defineProperty(event, 'pointerId', { value: 24 });
  fireEvent(element, event);
};

describe('DC-CEPH03B independent tracing overlays — render only drag preview', () => {
  const original = {
    capture: Object.getOwnPropertyDescriptor(Element.prototype, 'setPointerCapture'),
    point: Object.getOwnPropertyDescriptor(SVGSVGElement.prototype, 'createSVGPoint'),
    ctm: Object.getOwnPropertyDescriptor(SVGSVGElement.prototype, 'getScreenCTM'),
  };
  beforeEach(() => {
    commit.mockReset();
    Object.defineProperty(Element.prototype, 'setPointerCapture', {
      configurable: true, value: vi.fn(),
    });
    Object.defineProperty(SVGSVGElement.prototype, 'getScreenCTM', {
      configurable: true, value: () => ({ inverse: () => ({}) }),
    });
    Object.defineProperty(SVGSVGElement.prototype, 'createSVGPoint', {
      configurable: true, value: () => ({
        x: 0, y: 0,
        matrixTransform(this: { x: number; y: number }) { return { x: this.x, y: this.y }; },
      }),
    });
  });
  afterEach(() => {
    cleanup();
    for (const [target, key, value] of [
      [Element.prototype, 'setPointerCapture', original.capture],
      [SVGSVGElement.prototype, 'createSVGPoint', original.point],
      [SVGSVGElement.prototype, 'getScreenCTM', original.ctm],
    ] as const) {
      if (value) Object.defineProperty(target, key, value);
      else Reflect.deleteProperty(target, key);
    }
    vi.restoreAllMocks();
  });

  it('keeps infinitely extended guides out of the all-analyses overview', () => {
    render(<Fixture mode="all" />);
    expect(document.querySelectorAll('[data-cephalo-extended-line]')).toHaveLength(0);
    expect(document.querySelectorAll('[data-cephalo-line-key]')).not.toHaveLength(0);
  });

  it('COM Frankfort uses the live Porion position without committing and returns to baseline on cancel', () => {
    render(<Fixture mode="com" />);
    const fh = () => line('com-frankfort');
    const po = handle('Po');
    expect(fh().getAttribute('x1')).toBe('30');
    pointer(po, 'pointerdown', 30, 40);
    pointer(po, 'pointermove', 65, 75);
    expect(fh().getAttribute('x1')).toBe('65');
    expect(fh().getAttribute('y1')).toBe('75');
    expect(commit).not.toHaveBeenCalled();
    pointer(po, 'pointercancel');
    expect(fh().getAttribute('x1')).toBe('30');
    expect(fh().getAttribute('y1')).toBe('40');
    expect(commit).not.toHaveBeenCalled();
  });

  it('Ricketts overlay in Tous mode follows live N and rolls back on lost capture', () => {
    render(<Fixture mode="all" />);
    const npog = () => line('ricketts-n-pog');
    const n = handle('N');
    expect(npog().getAttribute('x1')).toBe('130');
    pointer(n, 'pointerdown', 130, 70);
    pointer(n, 'pointermove', 145, 90);
    expect(npog().getAttribute('x1')).toBe('145');
    expect(npog().getAttribute('y1')).toBe('90');
    expect(commit).not.toHaveBeenCalled();
    fireEvent(n, new Event('lostpointercapture', { bubbles: true }));
    expect(npog().getAttribute('x1')).toBe('130');
    expect(npog().getAttribute('y1')).toBe('70');
    expect(commit).not.toHaveBeenCalled();
  });

  it('COM commits the moved landmark exactly once only on pointerup', () => {
    render(<Fixture mode="com" />);
    const fh = () => line('com-frankfort');
    const po = handle('Po');
    pointer(po, 'pointerdown', 30, 40);
    pointer(po, 'pointermove', 50, 55);
    expect(commit).not.toHaveBeenCalled();
    pointer(po, 'pointerup', 50, 55);
    expect(commit).toHaveBeenCalledTimes(1);
    expect(fh().getAttribute('x1')).toBe('50');
    expect(fh().getAttribute('y1')).toBe('55');
    expect(commit.mock.calls[0][0].find((p: Landmark) => p.id === 'Or')).toEqual({ id: 'Or', x: 100, y: 42 });
  });
});
