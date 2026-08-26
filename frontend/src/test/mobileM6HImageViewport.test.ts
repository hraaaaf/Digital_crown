import { describe, expect, it } from 'vitest';
import {
  PANORAMIC_MAX_SCALE,
  PANORAMIC_RESET,
  clampPanoramicScale,
  clampPanoramicTransform,
  containedPanoramicSize,
  panPanoramicBy,
  zoomPanoramicAt,
} from '../features/mobile/Context/mobilePanoramicGeometry';

const geometry = { width: 360, height: 600, imageWidth: 1200, imageHeight: 600 };

describe('M6-H panoramic viewport geometry', () => {
  it('fits a panoramic image without cropping at 1x', () => {
    expect(containedPanoramicSize(geometry)).toEqual({ width: 360, height: 180 });
    expect(clampPanoramicTransform({ scale: 1, x: 99, y: -42 }, geometry)).toEqual(PANORAMIC_RESET);
  });

  it('bounds zoom between 1x and 4x', () => {
    expect(clampPanoramicScale(0.1)).toBe(1);
    expect(clampPanoramicScale(99)).toBe(PANORAMIC_MAX_SCALE);
  });

  it('keeps pan inside the visible image bounds', () => {
    const clamped = clampPanoramicTransform({ scale: 3, x: 999, y: 999 }, geometry);
    expect(clamped.scale).toBe(3);
    expect(clamped.x).toBe(360);
    expect(clamped.y).toBe(0);
  });

  it('zooms around the requested anchor and remains bounded', () => {
    const zoomed = zoomPanoramicAt(PANORAMIC_RESET, 2, { x: 40, y: 300 }, geometry);
    expect(zoomed.scale).toBe(2);
    expect(zoomed.x).toBeGreaterThan(0);
    expect(zoomed.x).toBeLessThanOrEqual(180);
  });

  it('pans only while zoomed and recenters when returning to 1x', () => {
    const moved = panPanoramicBy({ scale: 2, x: 0, y: 0 }, 500, 80, geometry);
    expect(moved.x).toBe(180);
    expect(moved.y).toBe(0);
    expect(clampPanoramicTransform({ ...moved, scale: 1 }, geometry)).toEqual(PANORAMIC_RESET);
  });
});
