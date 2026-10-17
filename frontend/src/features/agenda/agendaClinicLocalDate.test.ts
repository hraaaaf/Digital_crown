import { describe, expect, it } from 'vitest';
import { clinicCalendarDay, clinicLocalAppointmentTime } from './agendaClinicLocalDate';

describe('LOT07 P2 — clinic-local date invariants (runner-independent)', () => {
  it('preserves a date-only day created in the local clock', () => {
    const selectedDate = new Date(2026, 9, 17, 0, 20);
    expect(clinicCalendarDay(selectedDate)).toBe('2026-10-17');
  });

  it('constructs and formats a local datetime without changing the chosen date', () => {
    const instant = clinicLocalAppointmentTime('2026-10-17', 9, 30);
    expect(clinicCalendarDay(instant)).toBe('2026-10-17');
    expect(instant.getHours()).toBe(9);
    expect(instant.getMinutes()).toBe(30);
  });

  it('rejects invalid and rolled local date/time input', () => {
    expect(() => clinicLocalAppointmentTime('2026-02-30', 9, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 24, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 9, 60)).toThrow();
    expect(() => clinicCalendarDay(new Date(Number.NaN))).toThrow();
  });
});
