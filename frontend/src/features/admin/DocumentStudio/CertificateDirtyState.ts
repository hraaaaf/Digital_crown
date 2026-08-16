type DirtyListener = (dirty: boolean) => void;

let certificateDirty = false;
const listeners = new Set<DirtyListener>();

export function isCertificateDirty(): boolean {
  return certificateDirty;
}

export function setCertificateDirty(dirty: boolean): void {
  if (certificateDirty === dirty) return;
  certificateDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeCertificateDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
