type DirtyListener = (dirty: boolean) => void;

let libreDirty = false;
const listeners = new Set<DirtyListener>();

export function isLibreDirty(): boolean {
  return libreDirty;
}

export function setLibreDirty(dirty: boolean): void {
  if (libreDirty === dirty) return;
  libreDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeLibreDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
