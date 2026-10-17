import { describe, expect, it } from 'vitest';
import { clinicCalendarDay, clinicLocalAppointmentTime } from './agendaClinicLocalDate';

describe('LOT07 P2 — west-of-UTC time-zone regression', () => {
  it('fails if the test process is not configured for America/New_York', () => {
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe('America/New_York');
  });

  it('never shifts a date-only form field to the previous day west of UTC', () => {
    const local = clinicLocalAppointmentTime('2026-10-17', 0, 20);
    expect(clinicCalendarDay(local)).toBe('2026-10-17');
    expect(local.toISOString()).toBe('2026-10-17T04:20:00.000Z');
  });
});
