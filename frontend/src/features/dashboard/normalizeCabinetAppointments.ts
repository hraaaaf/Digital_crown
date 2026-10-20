/** LOT07/07-C: bridge the real FastAPI AppointmentOut wire into the
 * historical Signature Dashboard contract, without inventing patient data.
 * Patient identity must first be minimized by the backend for agenda-only
 * actors; we independently mask it here on client permission changes.
 */
import type { DashboardAppointment } from './types';

export function normalizeCabinetAppointments(
  payload: unknown,
  canReadPatients: boolean,
): DashboardAppointment[] {
  if (!Array.isArray(payload)) throw new Error('Agenda response must be an array');
  return payload.map((entry): DashboardAppointment => {
    if (entry === null || typeof entry !== 'object' || Array.isArray(entry)) {
      throw new Error('Invalid Cabinet appointment');
    }
    const wire = entry as Record<string, unknown>;
    const start = wire.datetime_start ?? wire.start_time;
    if (!Number.isSafeInteger(wire.id) || (wire.id as number) < 1 ||
        typeof start !== 'string' ||
        !/^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?$/.test(start) ||
        typeof wire.status !== 'string' || !wire.status.trim()) {
      throw new Error('Unverifiable Cabinet appointment');
    }
    const patientId = canReadPatients && Number.isSafeInteger(wire.patient_id) &&
      (wire.patient_id as number) > 0 ? wire.patient_id as number : null;
    const name = canReadPatients && typeof wire.patient_name === 'string'
      ? wire.patient_name.trim() : '';
    const legacy = canReadPatients && wire.patient && typeof wire.patient === 'object'
      ? wire.patient as DashboardAppointment['patient'] : null;
    // A canonical patient_name is a single field; do NOT guess name order.
    const patient = name ? { id: patientId ?? undefined, nom: name, prenom: '' } : legacy;
    return {
      id: wire.id as number,
      datetime_start: start,
      start_time: start,
      status: wire.status as string,
      ticket_number: Number.isInteger(wire.ticket_number) ? wire.ticket_number as number : null,
      patient_id: patientId,
      patient_name: name || null,
      patient: patient ?? null,
      description: canReadPatients && typeof wire.motif === 'string'
        ? wire.motif : canReadPatients && typeof wire.description === 'string'
          ? wire.description : null,
    } as DashboardAppointment;
  });
}
