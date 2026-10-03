import { describe, expect, it } from 'vitest';
import type { Landmark } from './cephaloShared';
import {
  applyLandmarkEdit,
  createLandmarkEditTimeline,
  redoLandmarkEdit,
  resetLandmarksToBaseline,
  undoLandmarkEdit,
} from './orthoLandmarkEditHistory';

const baseline: Landmark[] = [
  { id: 'S', x: 10, y: 20 },
  { id: 'N', x: 30, y: 40 },
];

describe('Orthodontic Studio LOT07 landmark edit history', () => {
  it('records a reversible edit with the changed landmark id', () => {
    const timeline = createLandmarkEditTimeline(baseline);
    const edited = baseline.map(item => item.id === 'N' ? { ...item, x: 35 } : item);
    const applied = applyLandmarkEdit(timeline, baseline, edited);

    expect(applied.changed).toBe(true);
    expect(applied.timeline.undoStack).toHaveLength(1);
    expect(applied.timeline.redoStack).toHaveLength(0);
    expect(applied.timeline.undoStack[0].changedLandmarkIds).toEqual(['N']);
    expect(applied.timeline.auditTrail[0].action).toBe('EDIT');

    const undone = undoLandmarkEdit(applied.timeline, applied.landmarks);
    expect(undone.landmarks).toEqual(baseline);
    expect(undone.timeline.auditTrail.at(-1)?.action).toBe('UNDO');

    const redone = redoLandmarkEdit(undone.timeline, undone.landmarks);
    expect(redone.landmarks).toEqual(edited);
    expect(redone.timeline.auditTrail.at(-1)?.action).toBe('REDO');
  });

  it('invalidates redo after a new branch edit without deleting the audit trail', () => {
    const first = applyLandmarkEdit(
      createLandmarkEditTimeline(baseline),
      baseline,
      baseline.map(item => item.id === 'S' ? { ...item, y: 25 } : item),
    );
    const undone = undoLandmarkEdit(first.timeline, first.landmarks);
    expect(undone.timeline.redoStack).toHaveLength(1);

    const branched = applyLandmarkEdit(
      undone.timeline,
      undone.landmarks,
      undone.landmarks.map(item => item.id === 'N' ? { ...item, y: 45 } : item),
    );
    expect(branched.timeline.redoStack).toHaveLength(0);
    expect(branched.timeline.auditTrail.map(item => item.action)).toEqual(['EDIT', 'UNDO', 'EDIT']);
  });

  it('makes reset-to-baseline an undoable audited transaction', () => {
    const edited = baseline.map(item => item.id === 'S' ? { ...item, x: 16 } : item);
    const first = applyLandmarkEdit(createLandmarkEditTimeline(baseline), baseline, edited);
    const reset = resetLandmarksToBaseline(first.timeline, first.landmarks);

    expect(reset.changed).toBe(true);
    expect(reset.landmarks).toEqual(baseline);
    expect(reset.timeline.auditTrail.at(-1)?.action).toBe('RESET_TO_BASELINE');

    const undoReset = undoLandmarkEdit(reset.timeline, reset.landmarks);
    expect(undoReset.landmarks).toEqual(edited);
  });

  it('is a no-op when coordinates are unchanged or no history exists', () => {
    const timeline = createLandmarkEditTimeline(baseline);
    expect(applyLandmarkEdit(timeline, baseline, baseline).changed).toBe(false);
    expect(undoLandmarkEdit(timeline, baseline).changed).toBe(false);
    expect(redoLandmarkEdit(timeline, baseline).changed).toBe(false);
    expect(resetLandmarksToBaseline(timeline, baseline).changed).toBe(false);
  });
});
