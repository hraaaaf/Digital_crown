import { afterEach, describe, expect, it } from 'vitest';
import { useOrthoStore } from './stores/useOrthoStore';

afterEach(() => {
  useOrthoStore.getState().resetLayers();
});

describe('Orthodontic Studio LOT07 layer state', () => {
  it('toggles T1 and T2 independently', () => {
    const store = useOrthoStore.getState();
    expect(store.layerVisibility.t1).toBe(false);
    expect(store.layerVisibility.t2).toBe(false);

    store.setLayerVisible('t1', true);
    expect(useOrthoStore.getState().layerVisibility.t1).toBe(true);
    expect(useOrthoStore.getState().layerVisibility.t2).toBe(false);

    store.setLayerVisible('t2', true);
    expect(useOrthoStore.getState().layerVisibility.t1).toBe(true);
    expect(useOrthoStore.getState().layerVisibility.t2).toBe(true);
  });

  it('clamps opacity through the store boundary', () => {
    const store = useOrthoStore.getState();
    store.setLayerOpacity('plans', -10);
    expect(useOrthoStore.getState().layerOpacity.plans).toBe(0.1);
    store.setLayerOpacity('plans', 10);
    expect(useOrthoStore.getState().layerOpacity.plans).toBe(1);
  });

  it('does not mutate clinical geometry or measurements when display state changes', () => {
    const store = useOrthoStore.getState();
    const localBefore = store.local;
    const anglesBefore = store.anglesData;

    store.toggleLayer('landmarks');
    store.setLayerOpacity('soft_tissue', 0.35);

    const after = useOrthoStore.getState();
    expect(after.local).toBe(localBefore);
    expect(after.anglesData).toBe(anglesBefore);
  });
});
