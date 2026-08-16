type DirtyListener = (dirty: boolean) => void;

let diagnosticCompanionDirty = false;
const listeners = new Set<DirtyListener>();

export function isDiagnosticCompanionDirty(): boolean {
  return diagnosticCompanionDirty;
}

export function setDiagnosticCompanionDirty(dirty: boolean): void {
  if (diagnosticCompanionDirty === dirty) return;
  diagnosticCompanionDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeDiagnosticCompanionDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
