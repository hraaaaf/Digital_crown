import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cephaloRepository } from './cephaloRepository';
import { useOrthoStore } from './stores/useOrthoStore';
import { createLandmarkEditTimeline } from './orthoLandmarkEditHistory';

vi.mock('./cephaloRepository', () => ({
  cephaloRepository: {
    saveAnalysis: vi.fn(async () => ({ status: 'success' })),
  },
}));

const baseline = [
  { id: 'S', x: 10, y: 20 },
  { id: 'N', x: 30, y: 40 },
];

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  useOrthoStore.setState({
    patientId: 1,
    analysisId: 42,
    local: { landmarks: baseline.map(item => ({ ...item })), version: 1 },
    landmarkEditTimeline: createLandmarkEditTimeline(baseline),
    syncState: 'idle',
  });
});

afterEach(() => {
  useOrthoStore.getState().clearSyncTimer();
  vi.useRealTimers();
});

describe('Orthodontic Studio LOT07 landmark edit store', () => {
  it('persists a stabilized edit and its undo through the audited analysis endpoint', async () => {
    const edited = baseline.map(item => item.id === 'N' ? { ...item, x: 36 } : item);

    useOrthoStore.getState().updateLandmarksOptimistic(edited);
    expect(useOrthoStore.getState().local.landmarks).toEqual(edited);
    expect(useOrthoStore.getState().landmarkEditTimeline.undoStack).toHaveLength(1);
    expect(useOrthoStore.getState().syncState).toBe('syncing');

    await vi.advanceTimersByTimeAsync(600);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(1);
    expect(cephaloRepository.saveAnalysis).toHaveBeenLastCalledWith(
      42,
      expect.objectContaining({ landmarks: edited }),
    );

    useOrthoStore.getState().undoLandmarkEdit();
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    expect(useOrthoStore.getState().landmarkEditTimeline.redoStack).toHaveLength(1);

    await vi.advanceTimersByTimeAsync(600);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(2);
    expect(cephaloRepository.saveAnalysis).toHaveBeenLastCalledWith(
      42,
      expect.objectContaining({ landmarks: baseline }),
    );
  });

  it('cancels a pending landmark save when the active patient changes', async () => {
    useOrthoStore.setState({ patientId: 1, analysisId: 42 });
    const edited = baseline.map(item => item.id === 'S' ? { ...item, x: 18 } : item);
    useOrthoStore.getState().updateLandmarksOptimistic(edited);

    useOrthoStore.getState().setPatientInfo(2, 'Patient B');
    useOrthoStore.setState({ analysisId: 43 });
    await vi.advanceTimersByTimeAsync(1000);

    expect(cephaloRepository.saveAnalysis).not.toHaveBeenCalled();
    expect(useOrthoStore.getState().patientId).toBe(2);
  });

  it('makes reset-to-baseline undoable and clears redo after a new edit', () => {
    const first = baseline.map(item => item.id === 'S' ? { ...item, y: 24 } : item);
    useOrthoStore.getState().updateLandmarksOptimistic(first);
    useOrthoStore.getState().undoLandmarkEdit();
    expect(useOrthoStore.getState().landmarkEditTimeline.redoStack).toHaveLength(1);

    const branch = baseline.map(item => item.id === 'N' ? { ...item, y: 48 } : item);
    useOrthoStore.getState().updateLandmarksOptimistic(branch);
    expect(useOrthoStore.getState().landmarkEditTimeline.redoStack).toHaveLength(0);

    useOrthoStore.getState().resetLandmarkEdits();
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    expect(useOrthoStore.getState().landmarkEditTimeline.auditTrail.at(-1)?.action).toBe('RESET_TO_BASELINE');

    useOrthoStore.getState().undoLandmarkEdit();
    expect(useOrthoStore.getState().local.landmarks).toEqual(branch);
  });
});
