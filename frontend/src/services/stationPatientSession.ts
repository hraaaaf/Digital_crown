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

export type StationAppointmentSummary = {
  appointmentId: number;
  datetimeStart: string;
  durationMinutes: number;
  schedulingType: 'EXACT_TIME' | 'MORNING' | 'AFTERNOON' | 'FULL_DAY';
  status: string;
};

export type StationTodayAppointments = {
  status: 'none' | 'single' | 'multiple';
  appointments: StationAppointmentSummary[];
  staffActionRequired: boolean;
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

  async todayAppointments(sessionId: string): Promise<StationTodayAppointments> {
    const { data } = await api.get<StationTodayAppointments>(`/workstation/patient-session/${sessionId}/appointments/today`);
    return data;
  },

  async requestStaffAssistance(sessionId: string): Promise<{ status: 'STAFF_NOTIFIED'; alertId: number }> {
    const { data } = await api.post(`/workstation/patient-session/${sessionId}/staff-assistance`);
    return data;
  },

  async arrive(sessionId: string, appointmentId: number): Promise<{ status: 'ARRIVED'; appointmentId: number }> {
    const { data } = await api.post(`/workstation/patient-session/${sessionId}/appointments/${appointmentId}/arrive`);
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
