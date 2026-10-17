import { describe, expect, it } from 'vitest';
import { clinicCalendarDay, clinicLocalAppointmentTime } from './agendaClinicLocalDate';

describe('LOT07 P2 — date-only input west/east timezone invariant', () => {
  it('retains selected day and clock time independently of a runner default', () => {
    const local = clinicLocalAppointmentTime('2026-10-17', 0, 20);
    expect(clinicCalendarDay(local)).toBe('2026-10-17');
    expect(local.getHours()).toBe(0);
    expect(local.getMinutes()).toBe(20);
  });
});
