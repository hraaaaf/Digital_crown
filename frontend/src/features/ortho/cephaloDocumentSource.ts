/** Identity-bound cephalometric document source; never select the newest study. */
import { cephaloRepository } from './cephaloRepository';

export interface BoundCephaloDocumentSource {
  analysis_id: number;
  expected_revision: number;
}

/** One immutable snapshot of the active, selected study. Clinical fields are passed
 * in the separate PDF payload, never used as permission to rewrite science. */
export interface SelectedScientificSnapshot {
  landmarks: ReadonlyArray<{ id: string; x: number; y: number }>;
  mmPerPixel: number | null;
}

/** Only an exact persisted source match can avoid a redundant scientific PUT.
 * Missing coordinates, duplicate IDs or a calibration discrepancy are NOT matches.
 * All mismatches preserve the existing strict-save / fail-closed path. */
function matchesPersistedScientificSnapshot(
  persisted: any,
  snapshot: SelectedScientificSnapshot,
): boolean {
  if (!Array.isArray(persisted?.landmarks_data) || !Array.isArray(snapshot?.landmarks)
      || persisted.landmarks_data.length === 0
      || persisted.landmarks_data.length !== snapshot.landmarks.length) return false;
  const ratio = persisted.mm_per_pixel ?? null;
  if (ratio !== snapshot.mmPerPixel) return false;
  const byId = new Map<string, {x: number; y: number}>();
  for (const p of persisted.landmarks_data) {
    if (typeof p?.id !== 'string' || !p.id
        || !Number.isFinite(p.x) || !Number.isFinite(p.y) || byId.has(p.id)) return false;
    byId.set(p.id, {x: p.x, y: p.y});
  }
  const seen = new Set<string>();
  for (const p of snapshot.landmarks) {
    if (typeof p?.id !== 'string' || !p.id || seen.has(p.id)
        || !Number.isFinite(p.x) || !Number.isFinite(p.y)) return false;
    seen.add(p.id);
    const saved = byId.get(p.id);
    if (!saved || saved.x !== p.x || saved.y !== p.y) return false;
  }
  return true;
}

function boundVerifiedRevision(selected: any, analysisId: number): BoundCephaloDocumentSource {
  if (selected?.id !== analysisId) throw new Error("L'étude sélectionnée a changé pendant la prévisualisation.");
  const revision = selected.angles_data?.scientific_read_path?.revision;
  if (!Number.isSafeInteger(revision) || revision <= 0) {
    throw new Error("La révision scientifique de cette étude n'est pas vérifiable.");
  }
  return {analysis_id: analysisId, expected_revision: revision};
}

export async function prepareBoundCephaloDocumentSource(
  patientId: number,
  analysisId: number,
  assertCurrentSelection: () => boolean,
  saveSelectedAnalysis: () => Promise<void>,
  readCurrentScientificSnapshot?: () => SelectedScientificSnapshot,
): Promise<BoundCephaloDocumentSource> {
  if (!Number.isSafeInteger(patientId) || patientId <= 0
      || !Number.isSafeInteger(analysisId) || analysisId <= 0 || !assertCurrentSelection()) {
    throw new Error("Identité de l'étude non vérifiée.");
  }

  if (readCurrentScientificSnapshot) {
    const persisted = await cephaloRepository.getAnalysis(analysisId);
    if (!assertCurrentSelection() || persisted?.id !== analysisId) {
      throw new Error("L'étude sélectionnée a changé pendant la prévisualisation.");
    }
    const currentSnapshot = readCurrentScientificSnapshot();
    if (matchesPersistedScientificSnapshot(persisted, currentSnapshot)) {
      // A pending local edit during the GET must never become a silent green.
      if (!assertCurrentSelection() ||
          !matchesPersistedScientificSnapshot(persisted, readCurrentScientificSnapshot())) {
        throw new Error("Les repères ont changé pendant la préparation du document.");
      }
      // Never perform a no-op PUT that mutates the signed scientific graph at
      // the same revision. The backend checks this revision again on PDF POST.
      return boundVerifiedRevision(persisted, analysisId);
    }
  }

  await saveSelectedAnalysis();
  if (!assertCurrentSelection()) throw new Error("L'étude sélectionnée a changé pendant la sauvegarde.");
  const selected = await cephaloRepository.getAnalysis(analysisId);
  if (!assertCurrentSelection()) throw new Error("L'étude sélectionnée a changé pendant la prévisualisation.");
  return boundVerifiedRevision(selected, analysisId);
}
