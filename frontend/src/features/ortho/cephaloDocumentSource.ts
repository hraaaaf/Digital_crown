/** Identity-bound cephalometric document source; never select the newest study. */
import { cephaloRepository } from './cephaloRepository';

export interface BoundCephaloDocumentSource {
  analysis_id: number;
  expected_revision: number;
}

export async function prepareBoundCephaloDocumentSource(
  patientId: number,
  analysisId: number,
  assertCurrentSelection: () => boolean,
  saveSelectedAnalysis: () => Promise<void>,
): Promise<BoundCephaloDocumentSource> {
  if (!Number.isSafeInteger(patientId) || patientId <= 0
      || !Number.isSafeInteger(analysisId) || analysisId <= 0 || !assertCurrentSelection()) {
    throw new Error("Identité de l'étude non vérifiée.");
  }
  await saveSelectedAnalysis();
  if (!assertCurrentSelection()) throw new Error("L'étude sélectionnée a changé pendant la sauvegarde.");
  const selected = await cephaloRepository.getAnalysis(analysisId);
  if (!assertCurrentSelection() || selected?.id !== analysisId) {
    throw new Error("L'étude sélectionnée a changé pendant la prévisualisation.");
  }
  const revision = selected.angles_data?.scientific_read_path?.revision;
  if (!Number.isSafeInteger(revision) || revision <= 0) {
    throw new Error("La révision scientifique de cette étude n'est pas vérifiable.");
  }
  return { analysis_id: analysisId, expected_revision: revision };
}
