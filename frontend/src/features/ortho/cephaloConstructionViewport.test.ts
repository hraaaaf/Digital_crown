import { describe, expect, it } from 'vitest';
import { getCephaloConstructionViewport, getCephaloZoomViewBox } from './cephaloConstructionViewport';

describe('visual-only cephalometric extended-line viewport', () => {
  const points = [
    { x: 220, y: 280 }, { x: 680, y: 300 },
    { x: 630, y: 930 }, { x: 260, y: 870 },
    { x: 530, y: 600 },
  ];
  it('bounds the infinite visual rays, preserving every anatomical point with a margin', () => {
    const before = JSON.stringify(points);
    const frame = getCephaloConstructionViewport(points, 1000, 1400);
    expect(frame.limited).toBe(true);
    expect(frame.x).toBeGreaterThan(0);
    expect(frame.y).toBeGreaterThan(0);
    expect(frame.x + frame.width).toBeLessThan(1000);
    expect(frame.y + frame.height).toBeLessThan(1400);
    for (const point of points) {
      expect(point.x).toBeGreaterThan(frame.x);
      expect(point.x).toBeLessThan(frame.x + frame.width);
      expect(point.y).toBeGreaterThan(frame.y);
      expect(point.y).toBeLessThan(frame.y + frame.height);
    }
    expect(JSON.stringify(points)).toBe(before);
  });
  it('refuses to infer clipping bounds from incomplete or invalid landmarks', () => {
    const whole = { x: 0, y: 0, width: 1000, height: 1400, limited: false };
    expect(getCephaloConstructionViewport(points.slice(0, 3), 1000, 1400)).toEqual(whole);
    expect(getCephaloConstructionViewport([{ x: Infinity, y: 200 }, ...points.slice(0, 3)], 1000, 1400)).toEqual(whole);
    expect(getCephaloConstructionViewport([], 1000, 1400)).toEqual(whole);
  });
  it('never extends beyond the source image even for edge landmarks', () => {
    const edge = getCephaloConstructionViewport([
      { x: 0, y: 0 }, { x: 990, y: 0 }, { x: 1000, y: 1400 }, { x: 0, y: 1399 },
    ], 1000, 1400);
    expect(edge).toEqual({ x: 0, y: 0, width: 1000, height: 1400, limited: false });
  });
});

describe('read-only zoom: identical base and overlay image coordinates', () => {
  it('uses the full image at 100% and a centered crop at 150% without modifying inputs', () => {
    const pan = { x: 0, y: 0 };
    expect(getCephaloZoomViewBox(1200, 900)).toBe('0 0 1200 900');
    expect(getCephaloZoomViewBox(1200, 900, 1.5, pan)).toBe('200 150 800 600');
    expect(pan).toEqual({ x: 0, y: 0 });
  });
  it('bounds 200% pan to the image and rejects invalid zoom/pan values', () => {
    expect(getCephaloZoomViewBox(1200, 900, 2, { x: -1, y: -1 })).toBe('0 0 600 450');
    expect(getCephaloZoomViewBox(1200, 900, 2, { x: 1, y: 1 })).toBe('600 450 600 450');
    expect(getCephaloZoomViewBox(1200, 900, 99, { x: 9, y: -9 })).toBe('600 0 600 450');
    expect(getCephaloZoomViewBox(1200, 900, NaN, { x: NaN, y: NaN })).toBe('0 0 1200 900');
  });
});
