/** LOT07 07-A — date-only input is a local clinic calendar day, never a UTC date. */
export function clinicCalendarDay(value: Date): string {
  if (!Number.isFinite(value.getTime())) throw new Error('Invalid clinic calendar date');
  const year = String(value.getFullYear()).padStart(4, '0');
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Convert a clinic-local date + clock time to an instant; refuse rollover/DST gaps. */
export function clinicLocalAppointmentTime(dateValue: string, hours: number, minutes: number): Date {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateValue);
  if (!match || !Number.isInteger(hours) || hours < 0 || hours > 23 ||
      !Number.isInteger(minutes) || minutes < 0 || minutes > 59) {
    throw new Error('Invalid local appointment date/time');
  }
  const [year, month, day] = match.slice(1).map(Number);
  const date = new Date(`${dateValue}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00`);
  if (!Number.isFinite(date.getTime()) || date.getFullYear() !== year ||
      date.getMonth() + 1 !== month || date.getDate() !== day ||
      date.getHours() !== hours || date.getMinutes() !== minutes) {
    throw new Error('Nonexistent local appointment date/time');
  }
  return date;
}
