import { api } from '../../services/api';

export interface SuperimpositionPixelROI {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OrthoSuperimpositionSource {
  timepoint_id: number;
  timepoint_ordinal: number;
  occurred_at: string;
  cephalo_analysis_id: number;
  is_calibrated: boolean;
  mm_per_pixel: number | null;
}

export interface OrthoSuperimpositionContext {
  patient_id: number;
  ortho_case_id: number;
  from_source: OrthoSuperimpositionSource;
  to_source: OrthoSuperimpositionSource;
  quantitative_mm_allowed: boolean;
  applicability_status: string;
  method_id: string;
  method_version: string;
  quality_status: 'ENGINE_ESTIMATE_ONLY';
  clinically_validated: false;
}

export interface OrthoSuperimpositionRegistration {
  method_id: string;
  method_version: string;
  quality_status: 'ENGINE_ESTIMATE_ONLY';
  clinically_validated: false;
  transform_direction: 'moving_to_reference';
  matrix: [[number, number, number], [number, number, number]];
  rotation_degrees: number;
  uniform_scale: number;
  translation_px: { x: number; y: number };
  good_match_count: number;
  inlier_count: number;
  reference_roi: SuperimpositionPixelROI;
  moving_roi: SuperimpositionPixelROI;
  reference_size_px: { width: number; height: number };
  moving_size_px: { width: number; height: number };
  algorithm: Record<string, unknown>;
}

export interface OrthoSuperimpositionEstimate {
  context: OrthoSuperimpositionContext;
  registration: OrthoSuperimpositionRegistration;
}

export async function fetchOrthoSuperimpositionContext(
  patientId: number,
  caseId: number,
  fromTimepointId: number,
  toTimepointId: number,
): Promise<OrthoSuperimpositionContext> {
  const { data } = await api.get<OrthoSuperimpositionContext>(
    `/patients/${patientId}/ortho-case/${caseId}/superimposition/context`,
    { params: { from_timepoint_id: fromTimepointId, to_timepoint_id: toTimepointId } },
  );
  return data;
}

export async function estimateOrthoSuperimposition(
  patientId: number,
  caseId: number,
  payload: {
    from_timepoint_id: number;
    to_timepoint_id: number;
    reference_roi: SuperimpositionPixelROI;
    moving_roi: SuperimpositionPixelROI;
  },
): Promise<OrthoSuperimpositionEstimate> {
  const { data } = await api.post<OrthoSuperimpositionEstimate>(
    `/patients/${patientId}/ortho-case/${caseId}/superimposition/estimate`,
    payload,
  );
  return data;
}
