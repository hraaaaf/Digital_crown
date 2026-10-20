/** LOT07/07-C — no new business authority: presentation-only projection of Dashboard appointments. */
import type { DashboardAppointment } from '../dashboard/types';

export function isCommandCabinetLabEnabled(dev: boolean, optIn: string | undefined): boolean {
  // Both conditions are mandatory. A production build cannot enable the laboratory.
  return dev === true && optIn === 'true';
}

// Dashboard's historical UI types describe start_time/patient. Real FastAPI
// AppointmentOut instead serializes datetime_start/patient_name. Accept both,
 // and validate actual runtime data before rendering.
type AppointmentWire = DashboardAppointment & {
  datetime_start?: unknown;
  patient_name?: unknown;
};

export interface ReadOnlyAppointmentRow {
  id: number;
  time: string;
  status: string;
  patientLabel: string;
}

export function projectReadOnlyAppointments(
  data: DashboardAppointment[] | null,
  canReadPatients: boolean,
): ReadOnlyAppointmentRow[] | null {
  // Never interpret malformed API data as "no appointments".
  if (!Array.isArray(data)) return null;

  const result: ReadOnlyAppointmentRow[] = [];
  for (const item of data) {
    if (!item || !Number.isSafeInteger(item.id) || item.id <= 0 ||
        typeof item.status !== 'string' || !item.status.trim()) return null;
    const wire = item as AppointmentWire;
    const start = wire.datetime_start !== undefined ? wire.datetime_start : wire.start_time;
    if (typeof start !== 'string') return null;

    // FastAPI's real AppointmentOut: datetime_start (cabinet naive wall clock).
    // Legacy Dashboard data: start_time. Never convert these via Date/UTC.
    const clock = /^\d{4}-\d{2}-\d{2}T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/.exec(start);
    if (!clock || Number(clock[1]) > 23 || Number(clock[2]) > 59) return null;

    let patientLabel = 'Rendez-vous';
    if (canReadPatients) {
      if (typeof wire.patient_name === 'string' && wire.patient_name.trim()) {
        patientLabel = wire.patient_name.trim();
      } else if (wire.patient && typeof wire.patient.nom === 'string' &&
                 typeof wire.patient.prenom === 'string') {
        const name = `${wire.patient.prenom.trim()} ${wire.patient.nom.trim()}`.trim();
        if (name) patientLabel = name;
      }
    }
    result.push({
      id: item.id,
      time: `${clock[1]}:${clock[2]}`,
      status: item.status,
      patientLabel,
    });
  }
  return result;
}
