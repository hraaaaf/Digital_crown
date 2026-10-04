import type { Landmark } from './cephaloShared';

export type LandmarkEditSource = 'POINTER_DRAG' | 'RESET_CONTROL';
export type LandmarkEditAuditAction = 'EDIT' | 'UNDO' | 'REDO' | 'RESET_TO_BASELINE';

export interface LandmarkEditTransaction {
  id: string;
  sequence: number;
  source: LandmarkEditSource;
  before: Landmark[];
  after: Landmark[];
  changedLandmarkIds: string[];
}

export interface LandmarkEditAuditEvent {
  sequence: number;
  action: LandmarkEditAuditAction;
  transactionId: string;
  changedLandmarkIds: string[];
}

export interface LandmarkEditTimeline {
  baseline: Landmark[];
  undoStack: LandmarkEditTransaction[];
  redoStack: LandmarkEditTransaction[];
  auditTrail: LandmarkEditAuditEvent[];
  nextSequence: number;
}

export interface LandmarkEditTransition {
  timeline: LandmarkEditTimeline;
  landmarks: Landmark[];
  changed: boolean;
}

const MAX_UNDO_DEPTH = 100;
const MAX_AUDIT_EVENTS = 500;

export const cloneLandmarks = (landmarks: Landmark[]): Landmark[] =>
  landmarks.map(item => ({ ...item }));

export const landmarkSnapshotsEqual = (a: Landmark[], b: Landmark[]): boolean => {
  if (a.length !== b.length) return false;
  const byId = new Map(b.map(item => [item.id, item]));
  return a.every(item => {
    const other = byId.get(item.id);
    return !!other
      && item.x === other.x
      && item.y === other.y
      && item.isAdjusted === other.isAdjusted
      && item.version === other.version;
  });
};

export const changedLandmarkIds = (before: Landmark[], after: Landmark[]): string[] => {
  const beforeById = new Map(before.map(item => [item.id, item]));
  const afterById = new Map(after.map(item => [item.id, item]));
  const ids = new Set([...beforeById.keys(), ...afterById.keys()]);
  return [...ids].filter(id => {
    const a = beforeById.get(id);
    const b = afterById.get(id);
    return !a || !b
      || a.x !== b.x
      || a.y !== b.y
      || a.isAdjusted !== b.isAdjusted
      || a.version !== b.version;
  }).sort();
};

const trimUndo = (items: LandmarkEditTransaction[]) => items.slice(-MAX_UNDO_DEPTH);
const trimAudit = (items: LandmarkEditAuditEvent[]) => items.slice(-MAX_AUDIT_EVENTS);

export const createLandmarkEditTimeline = (baseline: Landmark[] = []): LandmarkEditTimeline => ({
  baseline: cloneLandmarks(baseline),
  undoStack: [],
  redoStack: [],
  auditTrail: [],
  nextSequence: 1,
});

const withAudit = (
  timeline: LandmarkEditTimeline,
  action: LandmarkEditAuditAction,
  transaction: LandmarkEditTransaction,
): LandmarkEditTimeline => ({
  ...timeline,
  auditTrail: trimAudit([
    ...timeline.auditTrail,
    {
      sequence: timeline.nextSequence,
      action,
      transactionId: transaction.id,
      changedLandmarkIds: [...transaction.changedLandmarkIds],
    },
  ]),
  nextSequence: timeline.nextSequence + 1,
});

export const applyLandmarkEdit = (
  timeline: LandmarkEditTimeline,
  before: Landmark[],
  after: Landmark[],
  source: LandmarkEditSource = 'POINTER_DRAG',
): LandmarkEditTransition => {
  if (landmarkSnapshotsEqual(before, after)) {
    return { timeline, landmarks: cloneLandmarks(before), changed: false };
  }
  const sequence = timeline.nextSequence;
  const transaction: LandmarkEditTransaction = {
    id: `landmark-edit-${sequence}`,
    sequence,
    source,
    before: cloneLandmarks(before),
    after: cloneLandmarks(after),
    changedLandmarkIds: changedLandmarkIds(before, after),
  };
  const next = withAudit(
    {
      ...timeline,
      undoStack: trimUndo([...timeline.undoStack, transaction]),
      redoStack: [],
    },
    source === 'RESET_CONTROL' ? 'RESET_TO_BASELINE' : 'EDIT',
    transaction,
  );
  return { timeline: next, landmarks: cloneLandmarks(after), changed: true };
};

export const undoLandmarkEdit = (
  timeline: LandmarkEditTimeline,
  current: Landmark[],
): LandmarkEditTransition => {
  const transaction = timeline.undoStack.at(-1);
  if (!transaction) return { timeline, landmarks: cloneLandmarks(current), changed: false };
  const next = withAudit(
    {
      ...timeline,
      undoStack: timeline.undoStack.slice(0, -1),
      redoStack: [...timeline.redoStack, transaction],
    },
    'UNDO',
    transaction,
  );
  return { timeline: next, landmarks: cloneLandmarks(transaction.before), changed: true };
};

export const redoLandmarkEdit = (
  timeline: LandmarkEditTimeline,
  current: Landmark[],
): LandmarkEditTransition => {
  const transaction = timeline.redoStack.at(-1);
  if (!transaction) return { timeline, landmarks: cloneLandmarks(current), changed: false };
  const next = withAudit(
    {
      ...timeline,
      undoStack: trimUndo([...timeline.undoStack, transaction]),
      redoStack: timeline.redoStack.slice(0, -1),
    },
    'REDO',
    transaction,
  );
  return { timeline: next, landmarks: cloneLandmarks(transaction.after), changed: true };
};

export const resetLandmarksToBaseline = (
  timeline: LandmarkEditTimeline,
  current: Landmark[],
): LandmarkEditTransition => {
  if (!timeline.baseline.length || landmarkSnapshotsEqual(current, timeline.baseline)) {
    return { timeline, landmarks: cloneLandmarks(current), changed: false };
  }
  return applyLandmarkEdit(timeline, current, timeline.baseline, 'RESET_CONTROL');
};
