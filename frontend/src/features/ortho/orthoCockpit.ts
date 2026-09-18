import { api } from '../../services/api';

export interface OrthoCockpitCase {
  case_id: number;
  started_at: string;
  lifecycle_status: 'ACTIVE' | 'INTERRUPTED' | 'ABANDONED' | 'CLOSED';
  current_phase_key: string | null;
  closed_at: string | null;
  controls_count: number;
}

export interface OrthoCockpitControl {
  id: number;
  occurred_at: string;
  phase_key: string | null;
  notable_event: string | null;
  next_planned_step: string | null;
  next_control_at: string | null;
  appointment_id: number | null;
}

export interface OrthoCockpitAppointment {
  id: number;
  datetime_start: string;
  status: string;
  motif: string | null;
}

export interface OrthoCockpitTimepoint {
  id: number;
  ordinal: number;
  occurred_at: string;
  note: string | null;
  evidence_count: number;
}

export interface OrthoCockpitEvidence {
  kind: 'CEPHALO' | 'PANORAMIC' | 'CLINICAL_ASSET';
  ref_id: number;
  recorded_at: string | null;
  label: string;
  timepoint_ordinal: number;
}

export interface OrthoCockpit {
  patient_id: number;
  case: OrthoCockpitCase | null;
  latest_control: OrthoCockpitControl | null;
  next_appointment: OrthoCockpitAppointment | null;
  latest_timepoint: OrthoCockpitTimepoint | null;
  latest_cephalo: OrthoCockpitEvidence | null;
  latest_panoramic: OrthoCockpitEvidence | null;
  latest_clinical_asset: OrthoCockpitEvidence | null;
  attention: string[];
}

export async function fetchOrthoCockpit(patientId: number): Promise<OrthoCockpit> {
  const { data } = await api.get<OrthoCockpit>(`/patients/${patientId}/ortho-cockpit`);
  return data;
}
