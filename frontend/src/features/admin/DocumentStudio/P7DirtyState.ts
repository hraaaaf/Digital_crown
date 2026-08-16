type DirtyListener = (dirty: boolean) => void;

let p7Dirty = false;
const listeners = new Set<DirtyListener>();

export function isP7Dirty(): boolean {
  return p7Dirty;
}

export function setP7Dirty(dirty: boolean): void {
  if (p7Dirty === dirty) return;
  p7Dirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeP7Dirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
