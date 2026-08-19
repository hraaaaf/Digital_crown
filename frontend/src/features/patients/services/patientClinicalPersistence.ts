import { api } from '../../../services/api';
import type { OdontogramType, ToothSurfaceState } from '../../../components/odontogram/types';

export interface PersistedOdontogram {
  id: number;
  patient_id: number;
  dentition_type: OdontogramType;
  state: Record<number, ToothSurfaceState>;
  revision: number;
  updated_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ClinicalConclusion {
  id: number;
  patient_id: number;
  conclusion_text: string;
  proposal_text?: string | null;
  proposal_source?: string | null;
  validated_by: number;
  created_at: string;
}

export interface MasterPlanRevision {
  id: number;
  patient_id: number;
  plan_id: number;
  revision_number: number;
  steps_snapshot: Array<{
    title: string;
    assistant: string;
    status: string;
    date_str: string;
    order_index: number;
  }>;
  updated_by: number;
  created_at: string;
}

const normalizeOdontogramState = (raw: unknown): Record<number, ToothSurfaceState> => {
  if (!raw || typeof raw !== 'object') return {};
  return Object.fromEntries(
    Object.entries(raw as Record<string, ToothSurfaceState>)
      .map(([key, value]) => [Number(key), value])
      .filter(([key]) => Number.isInteger(key)),
  ) as Record<number, ToothSurfaceState>;
};

export const patientClinicalPersistence = {
  async getOdontogram(patientId: number): Promise<PersistedOdontogram | null> {
    const response = await api.get(`/patients/${patientId}/odontogram`);
    if (!response.data) return null;
    return {
      ...response.data,
      state: normalizeOdontogramState(response.data.state),
    } as PersistedOdontogram;
  },

  async saveOdontogram(
    patientId: number,
    input: {
      dentition_type: OdontogramType;
      state: Record<number, ToothSurfaceState>;
      expected_revision: number;
    },
  ): Promise<PersistedOdontogram> {
    const response = await api.put(`/patients/${patientId}/odontogram`, input);
    return {
      ...response.data,
      state: normalizeOdontogramState(response.data.state),
    } as PersistedOdontogram;
  },

  async listConclusions(patientId: number): Promise<ClinicalConclusion[]> {
    const response = await api.get(`/patients/${patientId}/clinical-conclusions`);
    return Array.isArray(response.data) ? response.data : [];
  },

  async createConclusion(
    patientId: number,
    input: {
      conclusion_text: string;
      proposal_text?: string | null;
      proposal_source?: string | null;
    },
  ): Promise<ClinicalConclusion> {
    const response = await api.post(`/patients/${patientId}/clinical-conclusions`, input);
    return response.data as ClinicalConclusion;
  },

  async listMasterPlanRevisions(patientId: number): Promise<MasterPlanRevision[]> {
    const response = await api.get(`/patients/${patientId}/master-plan/revisions`);
    return Array.isArray(response.data) ? response.data : [];
  },
};
