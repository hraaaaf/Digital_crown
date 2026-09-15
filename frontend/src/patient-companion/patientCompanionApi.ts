import { resolveApiBase } from '../services/apiBase';
import { getVerifiedPatientIdToken, signOutPatient } from './firebasePatientAuth';

const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};
const PATIENT_API_BASE = resolveApiBase(
  env.VITE_API_URL,
  typeof window !== 'undefined' ? window.location : undefined,
);

export interface PatientContext {
  access_id: string;
  relationship_type: 'SELF' | 'PARENT' | 'GUARDIAN' | 'CAREGIVER' | string;
  patient: {
    display_name: string;
    prenom: string | null;
    nom: string | null;
  };
}

export interface PatientAppointment {
  id: number;
  datetime_start: string;
  duration_minutes: number;
  motif: string;
  status: string;
  scheduling_type: string | null;
}

export interface PatientShare {
  share_id: string;
  resource_type: 'document' | 'media';
  resource_id: number;
  title?: string | null;
  document_type?: string | null;
  asset_type?: string | null;
  mime_type?: string | null;
  captured_at?: string | null;
  created_at?: string | null;
}

export class PatientCompanionApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'PatientCompanionApiError';
  }
}

async function failClosedInvalidPatientSession(): Promise<void> {
  await signOutPatient().catch(() => undefined);
  if (typeof window !== 'undefined') {
    window.location.replace('/patient-companion');
  }
}

async function patientRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getVerifiedPatientIdToken();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  headers.set('Authorization', `Firebase ${token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

  const response = await fetch(`${PATIENT_API_BASE}/api/patient-companion${path}`, {
    ...init,
    headers,
    credentials: 'omit',
    cache: 'no-store',
  });

  let payload: unknown = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    payload = await response.json().catch(() => null);
  }

  if (!response.ok) {
    const detail = payload && typeof payload === 'object' && 'detail' in payload
      ? String((payload as { detail?: unknown }).detail ?? '')
      : '';
    if (response.status === 401) {
      await failClosedInvalidPatientSession();
    }
    throw new PatientCompanionApiError(response.status, detail || 'Requête Patient Companion refusée.');
  }

  return payload as T;
}

export async function getPatientContexts(): Promise<PatientContext[]> {
  const result = await patientRequest<{ contexts: PatientContext[] }>('/me');
  return result.contexts;
}

export async function activatePatientCompanion(input: { token?: string; manual_code?: string }): Promise<PatientContext> {
  return patientRequest<PatientContext>('/activate', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function getPatientAppointments(accessId: string): Promise<PatientAppointment[]> {
  const result = await patientRequest<{ items: PatientAppointment[] }>(
    `/contexts/${encodeURIComponent(accessId)}/appointments`,
  );
  return result.items;
}

export async function getPatientShares(accessId: string): Promise<PatientShare[]> {
  const result = await patientRequest<{ items: PatientShare[] }>(
    `/contexts/${encodeURIComponent(accessId)}/shares`,
  );
  return result.items;
}

export const patientCompanionApi = {
  getContexts: getPatientContexts,
  activate: activatePatientCompanion,
  getAppointments: getPatientAppointments,
  getShares: getPatientShares,
};
