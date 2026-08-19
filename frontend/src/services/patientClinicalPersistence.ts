import { api } from './api';
import type { OdontogramType, ToothSurfaceState } from '../components/odontogram/types';

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

export interface SaveOdontogramPayload {
  dentition_type: OdontogramType;
  state: Record<number, ToothSurfaceState>;
  expected_revision: number;
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

export interface CreateClinicalConclusionPayload {
  conclusion_text: string;
  proposal_text?: string | null;
  proposal_source?: string | null;
}

export interface MasterPlanRevision {
  id: number;
  plan_id: number;
  patient_id: number;
  revision: number;
  steps_snapshot: Array<Record<string, unknown>>;
  updated_by?: number | null;
  created_at: string;
}

export const patientClinicalPersistence = {
  async getOdontogram(patientId: number): Promise<PersistedOdontogram | null> {
    const response = await api.get<PersistedOdontogram | null>(`/patients/${patientId}/odontogram`);
    return response.data;
  },

  async saveOdontogram(patientId: number, payload: SaveOdontogramPayload): Promise<PersistedOdontogram> {
    const response = await api.put<PersistedOdontogram>(`/patients/${patientId}/odontogram`, payload);
    return response.data;
  },

  async listConclusions(patientId: number, limit = 20): Promise<ClinicalConclusion[]> {
    const response = await api.get<ClinicalConclusion[]>(`/patients/${patientId}/clinical-conclusions`, {
      params: { limit },
    });
    return response.data;
  },

  async createConclusion(
    patientId: number,
    payload: CreateClinicalConclusionPayload,
  ): Promise<ClinicalConclusion> {
    const response = await api.post<ClinicalConclusion>(`/patients/${patientId}/clinical-conclusions`, payload);
    return response.data;
  },

  async listMasterPlanRevisions(patientId: number, limit = 20): Promise<MasterPlanRevision[]> {
    const response = await api.get<MasterPlanRevision[]>(`/patients/${patientId}/master-plan/revisions`, {
      params: { limit },
    });
    return response.data;
  },
};
