/**
 * Canonical Agenda contract: `appointments.datetime_start` is a naive
 * cabinet wall-clock timestamp (backend DateTime without timezone).
 *
 * Never use Date.toISOString() here: it silently converts user-selected
 * 10:00 Casablanca to 09:00Z and shifts midnight to yesterday.
 * Server _naive_datetime strips timezone rather than converting instants.
 */
export function formatAgendaWallClock(value: Date): string {
  if (!Number.isFinite(value.getTime())) {
    throw new Error('Invalid Agenda datetime');
  }
  const pad = (n: number) => String(n).padStart(2, '0');
  const millis = value.getMilliseconds();
  const suffix = millis ? `.${String(millis).padStart(3, '0')}` : '';
  return `${value.getFullYear()}-${pad(value.getMonth()+1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}${suffix}`;
}
