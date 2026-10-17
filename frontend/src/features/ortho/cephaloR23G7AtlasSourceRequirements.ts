/**
 * R23-G7: display-only evidence obligations for three source-locked Atlas rows.
 * Deliberately separate from generated LOT06 registry and ACTIVE runtime Focus.
 * This file MUST NOT publish geometry, measurement values or clinical authority.
 */
import atlas from '../../../../docs/audits/schemas/cephalo_r23g7_atlas33_source_dependencies_v1.json';
import type { R23G3PinnedDependency } from './cephaloR23G3PinnedRequirements';

export const R23G7_ATLAS_PROFILE_ID = 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1' as const;

export function findR23G7AtlasSourceRequirements(
  profileId: string,
  measurementId: string,
  presentLandmarkIds: readonly string[],
): R23G3PinnedDependency | null {
  if (profileId !== R23G7_ATLAS_PROFILE_ID ||
      atlas.protocol_id !== R23G7_ATLAS_PROFILE_ID ||
      atlas.authority !== 'SOURCE_DEPENDENCY_PREVIEW_ONLY__NOT_RUNTIME_MEASUREMENT_AUTHORITY') return null;
  // Exact case-sensitive canonical identity. No Po/Po_anatomic,
  // Pog/Pog_hard or other forbidden alias substitution.
  const record = atlas.measurements.find(row => row.measurement_id === measurementId);
  if (!record) return null;
  const present = new Set(presentLandmarkIds);
  return {
    measurementId: record.measurement_id,
    requiredLandmarks: [...record.required_landmarks],
    missingLandmarks: record.required_landmarks.filter(id => !present.has(id)),
    requiredConstructions: [...record.required_constructions],
    sourceContracts: [...record.source_contracts],
    availabilityGate: record.availability_gate,
  };
}
