import { api } from '../../services/api';

export type OrthoCompareEvidenceKind = 'CLINICAL_ASSET' | 'CEPHALO' | 'PANORAMIC';

export interface OrthoCompareEvidence {
  kind: OrthoCompareEvidenceKind;
  ref_id: number;
  recorded_at: string | null;
  label: string;
}

export interface OrthoCompareTimepoint {
  id: number;
  ordinal: number;
  occurred_at: string;
  note: string | null;
  evidences: OrthoCompareEvidence[];
}

export interface OrthoMeasurementDelta {
  key: string;
  label: string;
  unit: string;
  from_value: number;
  to_value: number;
  delta: number;
}

export type OrthoMeasurementStatus =
  | 'AVAILABLE'
  | 'AVAILABLE_ANGULAR_ONLY_LINEAR_UNCALIBRATED'
  | 'NO_COMMON_MEASUREMENTS'
  | 'NO_CEPHALO_PAIR'
  | 'AMBIGUOUS_CEPHALO_PAIR';

export interface OrthoLongitudinalCompare {
  patient_id: number;
  ortho_case_id: number;
  from_timepoint: OrthoCompareTimepoint;
  to_timepoint: OrthoCompareTimepoint;
  measurements: OrthoMeasurementDelta[];
  measurement_status: OrthoMeasurementStatus;
  interpretation_policy: 'NUMERIC_ONLY_CLINICIAN_INTERPRETATION';
}

export interface OrthoCaseSummary {
  id: number;
  patient_id: number;
  lifecycle_status: string;
  current_phase_key: string | null;
}

export interface OrthoTimepointEvidenceSummary {
  id: number;
  clinical_asset_id: number | null;
  cephalo_analysis_id: number | null;
  panoramic_analysis_id: number | null;
  created_by: number | null;
  created_at: string;
}

export interface OrthoTimepointSummary {
  id: number;
  ortho_case_id: number;
  patient_id: number;
  ordinal: number;
  occurred_at: string;
  note: string | null;
  evidences: OrthoTimepointEvidenceSummary[];
}

export async function fetchOrthoCase(patientId: number): Promise<OrthoCaseSummary | null> {
  try {
    const { data } = await api.get<OrthoCaseSummary>(`/patients/${patientId}/ortho-case`);
    return data;
  } catch (error: any) {
    if (error?.response?.status === 404) return null;
    throw error;
  }
}

export async function fetchOrthoTimepoints(
  patientId: number,
  caseId: number,
): Promise<OrthoTimepointSummary[]> {
  const { data } = await api.get<OrthoTimepointSummary[]>(
    `/patients/${patientId}/ortho-case/${caseId}/timepoints`,
  );
  return data;
}

export async function fetchOrthoLongitudinalCompare(
  patientId: number,
  caseId: number,
  fromOrdinal: number,
  toOrdinal: number,
): Promise<OrthoLongitudinalCompare> {
  const { data } = await api.get<OrthoLongitudinalCompare>(
    `/patients/${patientId}/ortho-case/${caseId}/compare`,
    { params: { from_ordinal: fromOrdinal, to_ordinal: toOrdinal } },
  );
  return data;
}
