import { describe, expect, it } from 'vitest';
import {
  ORTHO_LAYER_REGISTRY,
  clampLayerOpacity,
  createDefaultLayerOpacity,
  createDefaultLayerVisibility,
} from './orthoLayerRegistry';

describe('Orthodontic Studio LOT07 layer registry', () => {
  it('contains the eight canonical presentation layers exactly once', () => {
    const ids = ORTHO_LAYER_REGISTRY.map(layer => layer.id);
    expect(ids).toEqual([
      'landmarks',
      'plans',
      'hard_tissue',
      'teeth',
      'soft_tissue',
      'measurements',
      't1',
      't2',
    ]);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('keeps unimplemented hard-tissue contours fail-closed', () => {
    const hardTissue = ORTHO_LAYER_REGISTRY.find(layer => layer.id === 'hard_tissue');
    expect(hardTissue?.availability).toBe('planned');
    expect(hardTissue?.defaultVisible).toBe(false);
    expect(hardTissue?.authority).toBe('display_template_only');
  });

  it('preserves safe authority semantics for display layers', () => {
    const byId = Object.fromEntries(ORTHO_LAYER_REGISTRY.map(layer => [layer.id, layer]));
    expect(byId.landmarks.authority).toBe('derived_visualization');
    expect(byId.teeth.authority).toBe('display_template_only');
    expect(byId.soft_tissue.authority).toBe('display_template_only');
    expect(byId.t1.authority).toBe('derived_visualization');
    expect(byId.t2.authority).toBe('derived_visualization');
  });

  it('builds independent defaults and clamps opacity', () => {
    const visibility = createDefaultLayerVisibility();
    const opacity = createDefaultLayerOpacity();

    expect(visibility.landmarks).toBe(true);
    expect(visibility.t1).toBe(false);
    expect(visibility.t2).toBe(false);
    expect(opacity.soft_tissue).toBe(0.9);
    expect(clampLayerOpacity(-1)).toBe(0.1);
    expect(clampLayerOpacity(4)).toBe(1);
    expect(clampLayerOpacity(Number.NaN)).toBe(1);
  });
});
