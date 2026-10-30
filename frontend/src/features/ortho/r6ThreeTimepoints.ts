import type {
  OrthoLongitudinalCompare,
  OrthoTimepointSummary,
} from './orthoLongitudinalCompare';

/**
 * LOT07 R6 / 07.1.C — read-only canonical T0/T1/T2 trajectory.
 * Presentation projection only; access is ALWAYS enforced by the real patient API.
 * Never guess missing sources/dates, reuse evidence across stages or derive
 * treatment quality from numeric deltas.
 */
export type R6TrajectoryDenial =
  | 'SESSION_SCOPE_INVALID'
  | 'TIMEPOINT_SCOPE_MISMATCH'
  | 'T0_T1_T2_INCOMPLETE'
  | 'TIMEPOINT_DUPLICATED'
  | 'DATE_OR_ORDER_INVALID'
  | 'CANONICAL_SOURCE_MISSING'
  | 'SOURCE_REUSED';

export type R6SourceRef = Readonly<{
  kind: 'CLINICAL_ASSET' | 'CEPHALO' | 'PANORAMIC';
  refId: number;
}>;

export type R6TrajectoryPoint = Readonly<{
  id: number;
  ordinal: 0 | 1 | 2;
  occurred_at: string;
  sources: readonly R6SourceRef[];
}>;

export type R6Trajectory = Readonly<{
  patientId: number;
  caseId: number;
  points: readonly [R6TrajectoryPoint, R6TrajectoryPoint, R6TrajectoryPoint];
}>;

export type R6TrajectoryGate =
  | {ok: true; trajectory: R6Trajectory}
  | {ok: false; reason: R6TrajectoryDenial};

const positiveId = (id: unknown): id is number => Number.isSafeInteger(id) && Number(id) > 0;
const sourceKey = (kind: string, id: number) => kind + ':' + id;

export function gateR6ThreeTimepoints(
  patientId: number,
  caseId: number,
  values: readonly OrthoTimepointSummary[] | null | undefined,
): R6TrajectoryGate {
  if (!positiveId(patientId) || !positiveId(caseId) || !Array.isArray(values)) {
    return {ok:false,reason:'SESSION_SCOPE_INVALID'};
  }
  if (values.some(v => !v || v.patient_id !== patientId || v.ortho_case_id !== caseId)) {
    return {ok:false,reason:'TIMEPOINT_SCOPE_MISMATCH'};
  }
  if (values.some(v => !positiveId(v.id) || !Number.isSafeInteger(v.ordinal) || v.ordinal < 0)) {
    return {ok:false,reason:'DATE_OR_ORDER_INVALID'};
  }
  const ordinals = values.map(v => v.ordinal);
  if (new Set(ordinals).size !== ordinals.length ||
      new Set(values.map(v => v.id)).size !== values.length) {
    return {ok:false,reason:'TIMEPOINT_DUPLICATED'};
  }
  const byOrdinal = new Map(values.map(v => [v.ordinal,v]));
  const points = [byOrdinal.get(0),byOrdinal.get(1),byOrdinal.get(2)];
  if (points.some(v => !v)) return {ok:false,reason:'T0_T1_T2_INCOMPLETE'};
  const triple = points as [OrthoTimepointSummary,OrthoTimepointSummary,OrthoTimepointSummary];
  const dates = triple.map(v => Date.parse(v.occurred_at));
  if (dates.some(d => !Number.isFinite(d)) || !(dates[0] < dates[1] && dates[1] < dates[2])) {
    return {ok:false,reason:'DATE_OR_ORDER_INVALID'};
  }

  const globalSources = new Set<string>();
  for (const timepoint of triple) {
    if (!Array.isArray(timepoint.evidences) || timepoint.evidences.length === 0) {
      return {ok:false,reason:'CANONICAL_SOURCE_MISSING'};
    }
    const local = new Set<string>();
    for (const evidence of timepoint.evidences) {
      if (!evidence || !positiveId(evidence.id)) {
        return {ok:false,reason:'CANONICAL_SOURCE_MISSING'};
      }
      const linked: [string,number][] = [];
      if (positiveId(evidence.clinical_asset_id)) linked.push(['asset',evidence.clinical_asset_id]);
      if (positiveId(evidence.cephalo_analysis_id)) linked.push(['cephalo',evidence.cephalo_analysis_id]);
      if (positiveId(evidence.panoramic_analysis_id)) linked.push(['panoramic',evidence.panoramic_analysis_id]);
      // A timepoint evidence must point at exactly one canonical source.
      if (linked.length !== 1) return {ok:false,reason:'CANONICAL_SOURCE_MISSING'};
      const key = sourceKey(linked[0][0],linked[0][1]);
      if (local.has(key) || globalSources.has(key)) return {ok:false,reason:'SOURCE_REUSED'};
      local.add(key);
      globalSources.add(key);
    }
  }
  // Strict display projection: DO NOT copy note, created_by or free text to the
  // triptych view, emitted reports or patient-facing screenshots.
  const projectPoint = (point: OrthoTimepointSummary, ordinal: 0 | 1 | 2): R6TrajectoryPoint => ({
    id: point.id,
    ordinal,
    occurred_at: point.occurred_at,
    sources: point.evidences.map((evidence): R6SourceRef =>
      positiveId(evidence.cephalo_analysis_id)
        ? {kind:'CEPHALO',refId:evidence.cephalo_analysis_id}
        : positiveId(evidence.panoramic_analysis_id)
          ? {kind:'PANORAMIC',refId:evidence.panoramic_analysis_id}
          : {kind:'CLINICAL_ASSET',refId:evidence.clinical_asset_id!}),
  });
  const projected: [R6TrajectoryPoint,R6TrajectoryPoint,R6TrajectoryPoint] = [
    projectPoint(triple[0],0),
    projectPoint(triple[1],1),
    projectPoint(triple[2],2),
  ];
  return {ok:true,trajectory:{patientId,caseId,points:projected}};
}

/** Refuse stale React Query compare responses before any patient evidence is rendered. */
export function trustedR6Comparison(
  comparison: OrthoLongitudinalCompare | null | undefined,
  patientId: number,
  caseId: number,
  fromOrdinal: number | null,
  toOrdinal: number | null,
): comparison is OrthoLongitudinalCompare {
  return Boolean(
    comparison && positiveId(patientId) && positiveId(caseId) &&
    fromOrdinal !== null && toOrdinal !== null && fromOrdinal !== toOrdinal &&
    comparison.patient_id === patientId && comparison.ortho_case_id === caseId &&
    comparison.from_timepoint?.ordinal === fromOrdinal &&
    comparison.to_timepoint?.ordinal === toOrdinal &&
    positiveId(comparison.from_timepoint?.id) && positiveId(comparison.to_timepoint?.id) &&
    comparison.interpretation_policy === 'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
  );
}
