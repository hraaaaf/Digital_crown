type DirtyListener = (dirty: boolean) => void;

let prescriptionDirty = false;
const listeners = new Set<DirtyListener>();

export function isPrescriptionDirty(): boolean {
  return prescriptionDirty;
}

export function setPrescriptionDirty(dirty: boolean): void {
  if (prescriptionDirty === dirty) return;
  prescriptionDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribePrescriptionDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
