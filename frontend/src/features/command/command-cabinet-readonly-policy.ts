/** LOT07/07-C — no new business authority: presentation-only projection of Dashboard appointments. */
import type { DashboardAppointment } from '../dashboard/types';

export function isCommandCabinetLabEnabled(dev: boolean, optIn: string | undefined): boolean {
  // Both conditions are mandatory. A production build cannot enable the laboratory.
  return dev === true && optIn === 'true';
}

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
    if (
      !item || !Number.isSafeInteger(item.id) || item.id <= 0 ||
      typeof item.start_time !== 'string' ||
      typeof item.status !== 'string' || !item.status.trim()
    ) return null;

    // Cabinet stores appointment wall-clock strings; do not call Date/UTC conversion here.
    const clock = /T(\d{2}):(\d{2})/.exec(item.start_time);
    if (!clock || Number(clock[1]) > 23 || Number(clock[2]) > 59) return null;

    let patientLabel = 'Rendez-vous';
    if (canReadPatients && item.patient && typeof item.patient.nom === 'string' &&
        typeof item.patient.prenom === 'string') {
      const name = `${item.patient.prenom.trim()} ${item.patient.nom.trim()}`.trim();
      if (name) patientLabel = name;
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
