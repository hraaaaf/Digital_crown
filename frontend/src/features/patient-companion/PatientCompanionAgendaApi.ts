import { API_BASE } from '../../services/api';
import type { PatientAppointment, PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionAgendaTransport } from './PatientCompanionAgendaTransport';

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
  async appointments(pairing: PatientPairing): Promise<PatientAppointment[]> {
    if (pairing.remoteTransport?.relay) {
      const result = await PatientCompanionAgendaTransport.sendAgendaCommand(
        pairing,
        'agenda.list',
        {},
      );
      if (result.status !== 'ACCEPTED' || !Array.isArray(result.result.items)) {
        throw new Error('Agenda refusé par le cabinet.');
      }
      return result.result.items as PatientAppointment[];
    }
    const accessId = encodeURIComponent(pairing.context.access_id);
    const payload = await getJson<{ items: PatientAppointment[] }>(
      pairing,
      `/api/patient-companion/contexts/${accessId}/agenda`,
    );
    return payload.items;
  },

  async practitioners(pairing: PatientPairing): Promise<PatientAgendaPractitioner[]> {
    if (pairing.remoteTransport?.relay) {
      const result = await PatientCompanionAgendaTransport.sendAgendaCommand(
        pairing,
        'agenda.practitioners',
        {},
      );
      if (result.status !== 'ACCEPTED' || !Array.isArray(result.result.items)) {
        throw new Error('Liste des praticiens refusée par le cabinet.');
      }
      return result.result.items as PatientAgendaPractitioner[];
    }
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
    if (pairing.remoteTransport?.relay) {
      const result = await PatientCompanionAgendaTransport.sendAgendaCommand(
        pairing,
        'agenda.slots',
        {
          practitioner_ref: practitionerRef,
          day,
          duration_minutes: durationMinutes,
        },
      );
      if (result.status !== 'ACCEPTED' || !Array.isArray(result.result.items)) {
        throw new Error('Créneaux refusés par le cabinet.');
      }
      return result.result.items as PatientAgendaSlot[];
    }
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
