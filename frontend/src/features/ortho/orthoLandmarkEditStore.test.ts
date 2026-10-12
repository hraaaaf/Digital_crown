import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cephaloRepository } from './cephaloRepository';
import { useOrthoStore } from './stores/useOrthoStore';
import { createLandmarkEditTimeline } from './orthoLandmarkEditHistory';

vi.mock('./cephaloRepository', () => ({
  cephaloRepository: {
    saveAnalysis: vi.fn(async () => ({ status: 'success' })),
    getAnalysis: vi.fn(async () => ({ angles_data: { scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED' } }, calibration_data: null, is_calibrated: false, mm_per_pixel: null })),
  },
}));

const flushSaveQueue = async (turns = 8) => {
  for (let i = 0; i < turns; i += 1) await Promise.resolve();
};

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
  it('refreshes authoritative scientific read after a persisted edit', async () => {
    const edited = baseline.map(item => item.id === 'N' ? { ...item, y: 48 } : item);
    useOrthoStore.getState().updateLandmarksOptimistic(edited);
    await flushSaveQueue();
    expect(cephaloRepository.getAnalysis).toHaveBeenCalledWith(42);
    expect(useOrthoStore.getState().anglesData?.scientific_read_path?.authority).toBe('EVIDENCE_GRAPH_V1');
    expect(useOrthoStore.getState().anglesData?.scientific_read_path?.active_chain).toBe('VERIFIED');
  });

  it('persists a stabilized edit and its undo through the audited analysis endpoint', async () => {
    const edited = baseline.map(item => item.id === 'N' ? { ...item, x: 36 } : item);

    useOrthoStore.getState().updateLandmarksOptimistic(edited);
    expect(useOrthoStore.getState().local.landmarks).toEqual(edited);
    expect(useOrthoStore.getState().landmarkEditTimeline.undoStack).toHaveLength(1);
    expect(useOrthoStore.getState().syncState).toBe('syncing');

    await flushSaveQueue();
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(1);
    expect(cephaloRepository.saveAnalysis).toHaveBeenLastCalledWith(
      42,
      expect.objectContaining({ landmarks: edited }),
    );

    useOrthoStore.getState().undoLandmarkEdit();
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    expect(useOrthoStore.getState().landmarkEditTimeline.redoStack).toHaveLength(1);

    await flushSaveQueue();
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(2);
    expect(cephaloRepository.saveAnalysis).toHaveBeenLastCalledWith(
      42,
      expect.objectContaining({ landmarks: baseline }),
    );
  });

  it('persists a committed revision to its originating analysis after patient navigation', async () => {
    useOrthoStore.setState({ patientId: 1, analysisId: 42 });
    const edited = baseline.map(item => item.id === 'S' ? { ...item, x: 18 } : item);
    useOrthoStore.getState().updateLandmarksOptimistic(edited);

    useOrthoStore.getState().setPatientInfo(2, 'Patient B');
    useOrthoStore.setState({ analysisId: 43 });
    await flushSaveQueue();

    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(1);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledWith(
      42,
      expect.objectContaining({ landmarks: edited }),
    );
    expect(useOrthoStore.getState().patientId).toBe(2);
    expect(useOrthoStore.getState().syncState).not.toBe('success');
  });

  it('serializes rapid committed edits so no backend evidence revision is collapsed or reordered', async () => {
    let releaseFirst!: () => void;
    const firstPending = new Promise<void>(resolve => { releaseFirst = resolve; });
    vi.mocked(cephaloRepository.saveAnalysis)
      .mockImplementationOnce(async () => { await firstPending; return { status: 'success' } as any; })
      .mockResolvedValue({ status: 'success' } as any);

    const first = baseline.map(item => item.id === 'S' ? { ...item, x: 18 } : item);
    const second = first.map(item => item.id === 'N' ? { ...item, y: 49 } : item);

    useOrthoStore.getState().updateLandmarksOptimistic(first);
    useOrthoStore.getState().updateLandmarksOptimistic(second);
    await flushSaveQueue();

    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(1);
    expect(cephaloRepository.saveAnalysis).toHaveBeenNthCalledWith(
      1,
      42,
      expect.objectContaining({ landmarks: first }),
    );

    releaseFirst();
    await flushSaveQueue();

    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(2);
    expect(cephaloRepository.saveAnalysis).toHaveBeenNthCalledWith(
      2,
      42,
      expect.objectContaining({ landmarks: second }),
    );
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
  it('audits two same-tick keyboard nudges as distinct ordered transactions and persists both snapshots', async () => {
    const store = useOrthoStore.getState();
    store.nudgeLandmarkFromKeyboard('N', 1, 0, 240, 240);
    store.nudgeLandmarkFromKeyboard('N', 10, 0, 240, 240);
    const timeline = useOrthoStore.getState().landmarkEditTimeline;
    const current = useOrthoStore.getState().local.landmarks;
    expect(current.find(point => point.id === 'N')).toEqual({ id: 'N', x: 41, y: 40 });
    expect(timeline.undoStack).toHaveLength(2);
    expect(timeline.undoStack.map(entry => entry.source)).toEqual(['KEYBOARD_NUDGE', 'KEYBOARD_NUDGE']);
    expect(timeline.undoStack.map(entry => entry.changedLandmarkIds)).toEqual([['N'], ['N']]);
    expect(timeline.auditTrail.map(entry => entry.action)).toEqual(['EDIT','EDIT']);
    await flushSaveQueue(20);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(2);
    expect(vi.mocked(cephaloRepository.saveAnalysis).mock.calls.map(([,payload]) =>
      (payload as {landmarks: typeof baseline}).landmarks.find(point => point.id === 'N')?.x
    )).toEqual([31, 41]);
  });

  it('undoes and redoes a keyboard edit as distinct audited FIFO revisions, without moving other points', async () => {
    const store = useOrthoStore.getState();
    store.nudgeLandmarkFromKeyboard('N', 0, -10, 240, 240);
    expect(useOrthoStore.getState().local.landmarks).toEqual([
      baseline[0], { id: 'N', x: 30, y: 30 },
    ]);
    useOrthoStore.getState().undoLandmarkEdit();
    expect(useOrthoStore.getState().local.landmarks).toEqual(baseline);
    useOrthoStore.getState().redoLandmarkEdit();
    expect(useOrthoStore.getState().local.landmarks).toEqual([
      baseline[0], { id: 'N', x: 30, y: 30 },
    ]);
    const timeline = useOrthoStore.getState().landmarkEditTimeline;
    expect(timeline.auditTrail.map(entry => entry.action)).toEqual(['EDIT','UNDO','REDO']);
    expect(timeline.undoStack.at(-1)?.source).toBe('KEYBOARD_NUDGE');
    await flushSaveQueue(24);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(3);
    expect(vi.mocked(cephaloRepository.saveAnalysis).mock.calls.map(([,payload]) =>
      (payload as {landmarks: typeof baseline}).landmarks.find(point => point.id === 'N')?.y
    )).toEqual([30,40,30]);
  });

  it('rejects missing or invalid keyboard coordinates and respects both image bounds', async () => {
    const store = useOrthoStore.getState();
    store.nudgeLandmarkFromKeyboard('no-such-point', 1, 0, 240, 240);
    store.nudgeLandmarkFromKeyboard('N', Number.NaN, 0, 240, 240);
    store.nudgeLandmarkFromKeyboard('N', 1, 0, 0, 240);
    store.nudgeLandmarkFromKeyboard('N', 0, 0, 240, 240);
    expect(useOrthoStore.getState().landmarkEditTimeline.undoStack).toHaveLength(0);
    expect(cephaloRepository.saveAnalysis).not.toHaveBeenCalled();
    store.nudgeLandmarkFromKeyboard('N', -100, 1000, 240, 240);
    expect(useOrthoStore.getState().local.landmarks.find(point => point.id === 'N')).toEqual({id:'N',x:0,y:240});
    await flushSaveQueue(20);
    expect(cephaloRepository.saveAnalysis).toHaveBeenCalledTimes(1);
  });

});
