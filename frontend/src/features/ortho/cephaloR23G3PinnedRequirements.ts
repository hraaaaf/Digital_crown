/** R23-G3: exact source-locked LOT06 subset only, never inferred atlas dependencies. */
import { CEPHALO_LOT06_FOCUS_REGISTRY } from './cephaloLot06FocusRegistry.generated';

export interface R23G3PinnedDependency {
  measurementId: string;
  requiredLandmarks: readonly string[];
  missingLandmarks: string[];
  requiredConstructions: readonly string[];
  sourceContracts: readonly string[];
  availabilityGate: string;
}

export function findR23G3PinnedRequirements(
  measurementId: string,
  presentLandmarkIds: readonly string[],
): R23G3PinnedDependency | null {
  if (!Object.prototype.hasOwnProperty.call(CEPHALO_LOT06_FOCUS_REGISTRY, measurementId)) return null;
  const dependency = CEPHALO_LOT06_FOCUS_REGISTRY[measurementId as keyof typeof CEPHALO_LOT06_FOCUS_REGISTRY];
  // Exact case-preserving anatomical identities, never replace Po/Co/Pog.
  const present = new Set(presentLandmarkIds);
  return {
    measurementId: dependency.measurementId,
    requiredLandmarks: [...dependency.requiredLandmarks],
    missingLandmarks: dependency.requiredLandmarks.filter(id => !present.has(id)),
    requiredConstructions: [...dependency.requiredConstructions],
    sourceContracts: [...dependency.sourceContracts],
    availabilityGate: dependency.availabilityGate,
  };
}
