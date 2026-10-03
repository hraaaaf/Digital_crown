import {
  CEPHALO_LOT06_FOCUS_REGISTRY,
  type CephaloCanonicalFocusDependency,
} from './cephaloLot06FocusRegistry.generated';
import type { CephaloMetricFocus } from './cephaloAnalysisBridge';

export interface CanonicalMetricRecord {
  measurement_id?: string | null;
  canonical_measurement_id?: string | null;
  involved_points?: string[] | null;
  involved_lines?: string[] | null;
}

interface CanonicalProjectionItem {
  canonical_measurement_id?: string | null;
  measurement_refs?: string[] | null;
}

interface ScientificReadPath {
  authority?: string | null;
  active_chain?: string | null;
  canonical_measurements?: CanonicalProjectionItem[] | null;
}

export interface CanonicalMetricAnglesData {
  scientific_read_path?: ScientificReadPath | null;
}

export type CephaloCanonicalMeasurementId = keyof typeof CEPHALO_LOT06_FOCUS_REGISTRY;

const hasRegistryEntry = (id: string): id is CephaloCanonicalMeasurementId =>
  Object.prototype.hasOwnProperty.call(CEPHALO_LOT06_FOCUS_REGISTRY, id);

export const resolveCanonicalMeasurementId = (
  metric: CanonicalMetricRecord | undefined,
  anglesData: CanonicalMetricAnglesData | undefined,
): CephaloCanonicalMeasurementId | null => {
  const scientificReadPath = anglesData?.scientific_read_path;
  if (scientificReadPath?.authority !== 'EVIDENCE_GRAPH_V1') return null;

  const direct = metric?.canonical_measurement_id?.trim();
  if (direct && hasRegistryEntry(direct)) return direct;

  const measurementRef = metric?.measurement_id?.trim();
  if (!measurementRef) return null;
  const projected = scientificReadPath.canonical_measurements ?? [];
  for (const item of projected) {
    const canonicalId = item?.canonical_measurement_id?.trim();
    if (
      canonicalId
      && hasRegistryEntry(canonicalId)
      && Array.isArray(item.measurement_refs)
      && item.measurement_refs.includes(measurementRef)
    ) return canonicalId;
  }
  return null;
};

export const canonicalDependencyForMetric = (
  metric: CanonicalMetricRecord | undefined,
  anglesData: CanonicalMetricAnglesData | undefined,
): CephaloCanonicalFocusDependency | null => {
  const canonicalId = resolveCanonicalMeasurementId(metric, anglesData);
  return canonicalId ? CEPHALO_LOT06_FOCUS_REGISTRY[canonicalId] : null;
};

export const resolveCanonicalMetricFocus = (
  key: string,
  metric: CanonicalMetricRecord | undefined,
  anglesData: CanonicalMetricAnglesData | undefined,
): CephaloMetricFocus | null => {
  const dependency = canonicalDependencyForMetric(metric, anglesData);
  if (!dependency) return null;

  return {
    key,
    points: [...dependency.requiredLandmarks],
    // Only backend-provided visual line ids are accepted. LOT07 must not infer
    // rendered lines from landmark names or duplicate LOT06 constructions.
    lines: Array.isArray(metric?.involved_lines) ? [...metric.involved_lines] : [],
    canonicalMeasurementId: dependency.measurementId,
    constructionIds: [...dependency.requiredConstructions],
    sourceContracts: [...dependency.sourceContracts],
    availabilityGate: dependency.availabilityGate,
    authority: 'LOT06_EXECUTABLE_MEASUREMENT_CONTRACT',
  };
};

export const describeCanonicalMetricFocus = (focus: CephaloMetricFocus | null): string => {
  if (!focus?.canonicalMeasurementId) {
    return 'Géométrie canonique indisponible — focus désactivé.';
  }
  const landmarkText = focus.points.length ? 'Landmarks: ' + focus.points.join(', ') : 'Landmarks: aucun';
  const constructionText = focus.constructionIds?.length
    ? 'Constructions: ' + focus.constructionIds.join(', ')
    : 'Constructions: aucune';
  return focus.canonicalMeasurementId + ' · ' + landmarkText + ' · ' + constructionText;
};
