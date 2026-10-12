import { describe, expect, it } from 'vitest';
import { cephaloLabelFontSize, layoutCephaloLandmarkLabels } from './cephaloLabelLayout';

const points = [
  { id: 'N', x: 800, y: 450 }, { id: 'A', x: 806, y: 454 },
  { id: 'B', x: 810, y: 458 }, { id: 'Po', x: 300, y: 600 },
  { id: 'Or', x: 420, y: 590 }, { id: 'Me', x: 810, y: 790 },
];

describe('DC-CEPH-03B.3e label layout (visual only)', () => {
  it('removes ambient labels but preserves editable landmarks unchanged', () => {
    const before = JSON.stringify(points);
    const labels = layoutCephaloLandmarkLabels(points, new Set(), null, 1280, 900);
    expect(labels.size).toBe(0);
    expect(JSON.stringify(points)).toBe(before);
  });
  it('prioritizes focused landmark and prevents pairwise text box collisions', () => {
    const requested = new Set(points.map(p => p.id));
    const labels = layoutCephaloLandmarkLabels(points, requested, 'N', 1280, 900);
    expect(labels.has('N')).toBe(true);
    const boxes = [...labels.values()];
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i], b = boxes[j];
        const overlaps = a.x < b.x + b.width && a.x + a.width > b.x
          && a.y - a.height < b.y && a.y > b.y - b.height;
        expect(overlaps, a.id + ' and ' + b.id + ' collide').toBe(false);
      }
    }
    const shuffled = [...points].reverse();
    expect([...layoutCephaloLandmarkLabels(shuffled, requested, 'N', 1280, 900)])
      .toEqual([...labels]);
  });
  it('keeps label bounds within the raster while leaving edge points untouched', () => {
    const edge = [{ id: 'S', x: 0, y: 0 }, { id: 'N', x: 1000, y: 1255 }];
    const before = JSON.stringify(edge);
    const labels = layoutCephaloLandmarkLabels(edge, new Set(['S', 'N']), 'S', 1000, 1255);
    expect(labels.size).toBe(2);
    for (const label of labels.values()) {
      expect(label.x).toBeGreaterThanOrEqual(0);
      expect(label.y - label.height).toBeGreaterThanOrEqual(0);
      expect(label.x + label.width).toBeLessThanOrEqual(1000);
      expect(label.y).toBeLessThanOrEqual(1255);
    }
    expect(JSON.stringify(edge)).toBe(before);
  });
  it('fails closed on invalid raster dimensions and never displays non-finite labels', () => {
    expect(layoutCephaloLandmarkLabels(points, new Set(['N']), 'N', 0, 900).size).toBe(0);
    expect(layoutCephaloLandmarkLabels([{ id: 'N', x: NaN, y: 3 }],
      new Set(['N']), 'N', 1000, 1000).size).toBe(0);
    expect(cephaloLabelFontSize(2272, 1818)).toBeGreaterThan(18);
  });
});
