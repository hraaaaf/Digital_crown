import { api } from './api';

export type StationFallbackMode = 'phone_dob' | 'name_dob' | 'disabled';

export type StationPatientSessionCreated = {
  sessionId: string;
  handoffUrl: string;
  qrDataUrl: string;
  nfcPayload: string;
  expiresAt: string;
  fallbackMode: StationFallbackMode;
};

export type StationPatientSessionStatus =
  | { status: 'pending'; sessionId: string; expiresAt: string }
  | { status: 'identified'; sessionId: string; displayName: string; claimedAt: string }
  | { status: 'expired'; sessionId: string };

export type StationPatientFallbackPayload = {
  birthDate: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
};

export const stationPatientSessionService = {
  async create(): Promise<StationPatientSessionCreated> {
    const { data } = await api.post<StationPatientSessionCreated>('/workstation/patient-session');
    return data;
  },

  async status(sessionId: string): Promise<StationPatientSessionStatus> {
    const { data } = await api.get<StationPatientSessionStatus>(`/workstation/patient-session/${sessionId}`);
    return data;
  },

  async fallback(sessionId: string, payload: StationPatientFallbackPayload): Promise<{ status: 'identified'; sessionId: string; displayName: string }> {
    const { data } = await api.post(`/workstation/patient-session/${sessionId}/fallback`, payload);
    return data;
  },

  async purge(sessionId: string): Promise<void> {
    await api.post(`/workstation/patient-session/${sessionId}/purge`);
  },

  async getConfig(): Promise<{ fallbackMode: StationFallbackMode }> {
    const { data } = await api.get('/workstation/patient-session/config');
    return data;
  },

  async updateConfig(fallbackMode: StationFallbackMode, ownerPin: string): Promise<{ fallbackMode: StationFallbackMode }> {
    const { data } = await api.patch('/workstation/patient-session/config', { fallbackMode, ownerPin });
    return data;
  },
};
