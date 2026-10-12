import { act, cleanup, fireEvent, render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Landmark } from './cephaloShared';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import { cephaloRepository } from './cephaloRepository';
import { createLandmarkEditTimeline } from './orthoLandmarkEditHistory';
import { createDefaultLayerOpacity, createDefaultLayerVisibility } from './orthoLayerRegistry';
import { useOrthoStore } from './stores/useOrthoStore';

const ANATOMY: Landmark[] = [
  { id: 'S', x: 10, y: 20 }, { id: 'N', x: 30, y: 40 },
  { id: 'Po', x: 14, y: 30 }, { id: 'Or', x: 85, y: 29 },
  { id: 'A', x: 42, y: 90 }, { id: 'B', x: 52, y: 110 },
];
const PROJECTIONS = {
  t1_projection: { S: [12, 22], N: [32, 42], Po: [16, 32], Or: [87, 31] },
  t2_projection: { S: [17, 27], N: [37, 47], Po: [19, 35], Or: [91, 34] },
};

vi.mock('./cephaloRepository', () => ({
  cephaloRepository: {
    saveAnalysis: vi.fn(async () => ({ status: 'success' })),
    getAnalysis: vi.fn(async () => ({
      angles_data: {
        t1_projection: { S: [12, 22], N: [32, 42], Po: [16, 32], Or: [87, 31] },
        t2_projection: { S: [17, 27], N: [37, 47], Po: [19, 35], Or: [91, 34] },
        scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED' },
      },
      calibration_data: null, is_calibrated: false, mm_per_pixel: null,
    })),
  },
}));

function IntegratedDesktopStage({ analysis = 'all' }: { analysis?: 'all' | 'com' }) {
  const landmarks = useOrthoStore(state => state.local.landmarks);
  const anglesData = useOrthoStore(state => state.anglesData);
  const visibility = useOrthoStore(state => state.layerVisibility);
  const opacity = useOrthoStore(state => state.layerOpacity);
  const nudge = useOrthoStore(state => state.nudgeLandmarkFromKeyboard);
  const update = useOrthoStore(state => state.updateLandmarksOptimistic);
  const ghosts = (['t1','t2'] as const).flatMap(layer => {
    if (!visibility[layer]) return [];
    const projection = layer === 't1' ? anglesData?.t1_projection : anglesData?.t2_projection;
    if (!projection) return [];
    return [{
      layerId: layer,
      opacity: 1,
      color: layer === 't1' ? '#6485cf' : '#51a392',
      landmarks: Object.entries(projection).map(([id,coords]) => ({
        id, x: (coords as [number, number])[0], y: (coords as [number, number])[1],
      })),
    }];
  });
  return (
    <div style={{ position: 'relative', width: 400, height: 320 }}>
      <CephaloTracingLayer
        landmarks={landmarks}
        ghosts={ghosts}
        imageWidth={240}
        imageHeight={240}
        onUpdateLandmarks={update}
        onKeyboardNudgeLandmark={nudge}
        magnifierEnabled={false}
        activeAnalysis={analysis}
        layerPresentation={{ visibility, opacity }}
        performanceMode
      />
    </div>
  );
}

const landmarkN = () => {
  const handle = document.querySelector('[data-ceph03b-drag-handle="N"]');
  if (!handle) throw Error('Missing editable N reticle');
  return handle;
};
const ghostSN = () => Array.from(document.querySelectorAll('[data-cephalo-line-key="sn"]'))
  .filter(node => node.getAttribute('stroke-dasharray') === '6,4');
const ghostCoordinates = () => ghostSN().map(node => [
  node.getAttribute('x1'), node.getAttribute('y1'),
  node.getAttribute('x2'), node.getAttribute('y2'),
]);

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  useOrthoStore.setState({
    patientId: 7,
    analysisId: 123,
    local: { landmarks: ANATOMY.map(p => ({ ...p })), version: 1 },
    anglesData: { ...PROJECTIONS },
    landmarkEditTimeline: createLandmarkEditTimeline(ANATOMY),
    layerVisibility: { ...createDefaultLayerVisibility(), t1: true, t2: true },
    layerOpacity: createDefaultLayerOpacity(),
    activeMorphing: 'none',
    syncState: 'idle',
  });
});

afterEach(() => {
  cleanup();
  useOrthoStore.getState().clearSyncTimer();
  vi.useRealTimers();
});

const flushSaves = async () => { for (let i = 0; i < 28; i++) await Promise.resolve(); };

describe('DC-CEPH-03B.3 clinical store + desktop keyboard + immutable T1/T2 projections', () => {
  it('preserves T1 and T2 projection geometry across two rapid keyboard events, undo and redo', async () => {
    render(<IntegratedDesktopStage />);
    expect(ghostSN()).toHaveLength(2);
    const immutableGhosts = ghostCoordinates();
    const handle = landmarkN();
    act(() => {
      fireEvent.keyDown(handle, { key: 'ArrowRight' });
      fireEvent.keyDown(handle, { key: 'ArrowRight' });
    });
    expect(useOrthoStore.getState().local.landmarks.find(p => p.id === 'N')?.x).toBe(32);
    expect(useOrthoStore.getState().landmarkEditTimeline.undoStack.map(t => t.source))
      .toEqual(['KEYBOARD_NUDGE','KEYBOARD_NUDGE']);
    expect(ghostCoordinates()).toEqual(immutableGhosts);
    act(() => { useOrthoStore.getState().undoLandmarkEdit(); });
    expect(useOrthoStore.getState().local.landmarks.find(p => p.id === 'N')?.x).toBe(31);
    expect(ghostCoordinates()).toEqual(immutableGhosts);
    act(() => { useOrthoStore.getState().redoLandmarkEdit(); });
    expect(useOrthoStore.getState().local.landmarks.find(p => p.id === 'N')?.x).toBe(32);
    expect(ghostCoordinates()).toEqual(immutableGhosts);
    await flushSaves();
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(4);
    expect(vi.mocked(cephaloRepository.saveAnalysis).mock.calls.map(([,payload]) =>
      (payload as {landmarks: Landmark[]}).landmarks.find(p => p.id === 'N')?.x
    )).toEqual([31,32,31,32]);
  });

  it('toggles T1 and T2 independently without editing landmarks or persisting ghost geometry', async () => {
    render(<IntegratedDesktopStage />);
    expect(ghostSN()).toHaveLength(2);
    const baseline = useOrthoStore.getState().local.landmarks;
    act(() => { useOrthoStore.getState().setLayerVisible('t1', false); });
    expect(ghostSN()).toHaveLength(1);
    act(() => { useOrthoStore.getState().setLayerVisible('t2', false); });
    expect(ghostSN()).toHaveLength(0);
    act(() => { useOrthoStore.getState().setLayerVisible('t1', true); });
    expect(ghostSN()).toHaveLength(1);
    act(() => { useOrthoStore.getState().setLayerVisible('t2', true); });
    expect(ghostSN()).toHaveLength(2);
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    await flushSaves();
    expect(cephaloRepository.saveAnalysis).not.toHaveBeenCalled();
    expect(useOrthoStore.getState().landmarkEditTimeline.undoStack).toHaveLength(0);
  });
  it('renders real visual-only T1/T2 ghost groups independently in COM without changing authoritative landmarks', () => {
    render(<IntegratedDesktopStage analysis="com" />);
    const trace = (id: 't1' | 't2') =>
      document.querySelector('[data-ceph03b-ghost-layer="' + id + '"]');
    const lines = (id: 't1' | 't2') => trace(id)?.querySelectorAll('line').length ?? 0;
    const baseline = useOrthoStore.getState().local.landmarks;
    expect(lines('t1')).toBeGreaterThan(0);
    expect(lines('t2')).toBeGreaterThan(0);
    const t2before = lines('t2');
    act(() => { useOrthoStore.getState().setLayerVisible('t1', false); });
    expect(lines('t1')).toBe(0);
    expect(lines('t2')).toBe(t2before);
    act(() => { useOrthoStore.getState().setLayerVisible('t2', false); });
    expect(lines('t2')).toBe(0);
    act(() => {
      useOrthoStore.getState().setLayerVisible('t1', true);
      useOrthoStore.getState().setLayerVisible('t2', true);
    });
    expect(lines('t1')).toBeGreaterThan(0);
    expect(lines('t2')).toBeGreaterThan(0);
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    expect(cephaloRepository.saveAnalysis).not.toHaveBeenCalled();
  });

});
