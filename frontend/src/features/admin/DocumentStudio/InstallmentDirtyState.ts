type DirtyListener = (dirty: boolean) => void;

let installmentDirty = false;
const listeners = new Set<DirtyListener>();

export function isInstallmentDirty(): boolean {
  return installmentDirty;
}

export function setInstallmentDirty(dirty: boolean): void {
  if (installmentDirty === dirty) return;
  installmentDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeInstallmentDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
