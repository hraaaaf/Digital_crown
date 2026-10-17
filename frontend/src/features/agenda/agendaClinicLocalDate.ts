/**
 * Agenda A1-A4 API contract: datetime_start is a CABINET WALL-CLOCK datetime
 * persisted as timezone-naive by backend/routers/appointments.py::_naive_datetime.
 *
 * This is NOT a UTC instant. Do not append Z, call toISOString(), or depend on
 * the browser's timezone. An explicit cabinet IANA timezone and migration are
 * tracked by Agenda A5, not silently introduced in LOT07.
 */
export function clinicCalendarDay(value: Date): string {
  if (!Number.isFinite(value.getTime())) throw new Error('Invalid calendar date');
  const year = String(value.getFullYear()).padStart(4, '0');
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function clinicAppointmentWallTime(dateValue: string, hours: number, minutes: number): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateValue);
  if (!match || !Number.isInteger(hours) || hours < 0 || hours > 23 ||
      !Number.isInteger(minutes) || minutes < 0 || minutes > 59) {
    throw new Error('Invalid cabinet appointment date/time');
  }
  const [year, month, day] = match.slice(1).map(Number);
  // UTC here is used ONLY to validate the Gregorian date without local TZ/DST.
  // It is never used to serialize the appointment into an instant.
  const check = new Date(Date.UTC(year, month - 1, day));
  if (year < 100 || check.getUTCFullYear() !== year ||
      check.getUTCMonth() + 1 !== month || check.getUTCDate() !== day) {
    throw new Error('Invalid cabinet calendar day');
  }
  return `${dateValue}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00`;
}

/** Read the wall-clock date and time the existing backend actually stores. */
export function clinicAppointmentFormFields(value: string): { date: string; time: string } {
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?$/.exec(value);
  if (!match) throw new Error('Invalid backend appointment datetime');
  clinicAppointmentWallTime(match[1], Number(match[2]), Number(match[3]));
  return { date: match[1], time: `${match[2]}:${match[3]}` };
}
