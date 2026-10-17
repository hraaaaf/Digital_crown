/**
 * R23-G8/W2 Atlas-only preview of original dental/manual SOURCE OBLIGATIONS.
 * This helper neither computes clinical measurements nor emits geometry Focus.
 */
import dental from '../../../../docs/audits/schemas/cephalo_r23g8_w2_atlas33_dental_manual_dependencies_v1.json';
import type { R23G3PinnedDependency } from './cephaloR23G3PinnedRequirements';

export interface R23G8W2DentalRequirement extends R23G3PinnedDependency {
  readonly requiredManualLandmarks: readonly string[];
  readonly indirectConstructionManualLandmarks: readonly string[];
  readonly requiresCalibration: boolean;
  readonly requiresSameImageSource: true;
  readonly clinicalEvidenceVerifiedByThisPreview: false;
}

export function findR23G8W2DentalRequirements(
  profileId: string,
  measurementId: string,
  presentLandmarkIds: readonly string[],
): R23G8W2DentalRequirement | null {
  if (profileId !== 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1' ||
      dental.protocol_id !== profileId ||
      dental.authority !== 'SOURCE_DENTAL_MANUAL_OBLIGATIONS_PREVIEW_ONLY__NO_MEASUREMENT_AUTHORITY') return null;
  const row = dental.measurements.find(item => item.measurement_id === measurementId);
  if (!row || row.requires_same_image_source !== true) return null;
  const present = new Set(presentLandmarkIds);
  return {
    measurementId: row.measurement_id,
    requiredLandmarks: [...row.required_landmarks],
    missingLandmarks: row.required_landmarks.filter(id => !present.has(id)),
    requiredConstructions: [...row.required_constructions],
    requiredManualLandmarks: [...row.required_manual_landmarks],
    indirectConstructionManualLandmarks: [...row.indirect_construction_manual_landmarks],
    requiresCalibration: row.requires_calibration,
    requiresSameImageSource: true,
    clinicalEvidenceVerifiedByThisPreview: false,
    sourceContracts: [...row.source_contracts],
    availabilityGate: row.availability_gate,
  };
}
