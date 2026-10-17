/** R23-G8 W3: read-only provenance obligations for the final 11 Atlas33 rows.
 * Names and declared presence are NOT patient-specific proof, a value or Focus.
 */
import cranio from '../../../../docs/audits/schemas/cephalo_r23g8_w3_atlas33_craniomandibular_dependencies_v1.json';
import type { R23G3PinnedDependency } from './cephaloR23G3PinnedRequirements';

export interface R23G8W3CranioRequirement extends R23G3PinnedDependency {
  readonly constructionTransitiveLandmarks: Readonly<Record<string, readonly string[]>>;
  readonly constructionDependencyChain: Readonly<Record<string, readonly string[]>>;
  readonly requiredManualLandmarks: readonly string[];
  readonly requiresCalibration: boolean;
  readonly requiresSameImageSource: true;
  readonly clinicalEvidenceVerifiedByThisPreview: false;
}

export function findR23G8W3CranioRequirements(
  profileId: string,
  measurementId: string,
  presentLandmarkIds: readonly string[],
): R23G8W3CranioRequirement | null {
  if (profileId !== 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1' ||
      cranio.protocol_id !== profileId ||
      cranio.authority !== 'SOURCE_CRANIOMANDIBULAR_OBLIGATIONS_PREVIEW_ONLY__NO_RUNTIME_AUTHORITY' ||
      cranio.clinical_release !== false) return null;
  const row = cranio.measurements.find(rec => rec.measurement_id === measurementId);
  if (!row || row.requires_same_image_source !== true) return null;
  const present = new Set(presentLandmarkIds);
  return {
    measurementId: row.measurement_id,
    requiredLandmarks: [...row.required_landmarks],
    missingLandmarks: row.required_landmarks.filter(id => !present.has(id)),
    requiredConstructions: [...row.required_constructions],
    constructionTransitiveLandmarks: Object.fromEntries(
      Object.entries(row.construction_transitive_landmarks).map(([key, points]) => [key, [...points]])),
    constructionDependencyChain: Object.fromEntries(
      Object.entries(row.construction_dependency_chain).map(([key, chain]) => [key, [...chain]])),
    requiredManualLandmarks: [...row.required_manual_landmarks],
    requiresCalibration: row.requires_calibration,
    requiresSameImageSource: true,
    clinicalEvidenceVerifiedByThisPreview: false,
    sourceContracts: [...row.source_contracts],
    availabilityGate: row.availability_gate,
  };
}
