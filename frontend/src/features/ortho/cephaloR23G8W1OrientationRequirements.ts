/**
 * R23-G8 W1 — Atlas2009 SIGNED orientation dependencies.
 * Display-only source obligations. NEVER infer that the active cephalogram
 * contains valid ImageOrientationEvidence or that a clinical Focus exists.
 */
import atlas from '../../../../docs/audits/schemas/cephalo_r23g8_w1_atlas33_orientation_dependencies_v1.json';
import type { R23G3PinnedDependency } from './cephaloR23G3PinnedRequirements';

export interface R23G8W1OrientationDependency extends R23G3PinnedDependency {
  readonly requiredManualLandmarks: readonly string[];
  readonly requiresCalibration: boolean;
  readonly sameImageOrientationEvidenceRequired: true;
  readonly orientationEvidenceVerifiedByThisPreview: false;
}

export function findR23G8W1OrientationRequirements(
  profileId: string,
  measurementId: string,
  presentLandmarkIds: readonly string[],
): R23G8W1OrientationDependency | null {
  if (profileId !== 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1' ||
      atlas.protocol_id !== profileId ||
      atlas.authority !== 'SOURCE_ORIENTATION_OBLIGATIONS_PREVIEW_ONLY__NOT_RUNTIME_MEASUREMENT_AUTHORITY') return null;
  // Exact source names only. Never treat Po as Po_anatomic; no implicit
  // screen-Y handedness, mirror state or active-graph orientation checks.
  const rec = atlas.measurements.find(row => row.measurement_id === measurementId);
  if (!rec || rec.requires_same_image_orientation !== true) return null;
  const present = new Set(presentLandmarkIds);
  return {
    measurementId: rec.measurement_id,
    requiredLandmarks: [...rec.required_landmarks],
    missingLandmarks: rec.required_landmarks.filter(id => !present.has(id)),
    requiredConstructions: [...rec.required_constructions],
    sourceContracts: [...rec.source_contracts],
    availabilityGate: rec.availability_gate,
    requiredManualLandmarks: [...rec.required_manual_landmarks],
    requiresCalibration: rec.requires_calibration,
    sameImageOrientationEvidenceRequired: true,
    orientationEvidenceVerifiedByThisPreview: false,
  };
}
