import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';

export type PatientAgendaPractitioner = {
  practitioner_ref: string;
  display_name: string;
};

export type PatientAgendaSlot = {
  slot_ref: string;
  datetime_start: string;
  duration_minutes: number;
  expires_at: string;
};

async function getJson<T>(pairing: PatientPairing, path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${pairing.accessToken}` },
    cache: 'no-store',
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || 'Chargement agenda Patient Companion impossible.');
    Object.assign(error, { status: response.status });
    throw error;
  }
  return payload as T;
}

export const PatientCompanionAgendaApi = {
  async practitioners(pairing: PatientPairing): Promise<PatientAgendaPractitioner[]> {
    const accessId = encodeURIComponent(pairing.context.access_id);
    const payload = await getJson<{ items: PatientAgendaPractitioner[] }>(
      pairing,
      `/api/patient-companion/contexts/${accessId}/agenda/practitioners`,
    );
    return payload.items;
  },

  async slots(
    pairing: PatientPairing,
    practitionerRef: string,
    day: string,
    durationMinutes = 30,
  ): Promise<PatientAgendaSlot[]> {
    const accessId = encodeURIComponent(pairing.context.access_id);
    const params = new URLSearchParams({
      practitioner_ref: practitionerRef,
      day,
      duration_minutes: String(durationMinutes),
    });
    const payload = await getJson<{ items: PatientAgendaSlot[] }>(
      pairing,
      `/api/patient-companion/contexts/${accessId}/agenda/slots?${params.toString()}`,
    );
    return payload.items;
  },
};
