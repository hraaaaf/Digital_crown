import { describe, expect, it } from 'vitest';
import { clinicCalendarDay, clinicLocalAppointmentTime } from './agendaClinicLocalDate';

describe('LOT07 P2 — Africa/Casablanca local date regression', () => {
  it('fails explicitly if the runner is not using Casablanca timezone', () => {
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe('Africa/Casablanca');
  });

  it('uses the Casablanca calendar day for creation near local midnight', () => {
    const selectedDate = new Date(2026, 9, 17, 0, 20);
    expect(selectedDate.toISOString().slice(0, 10)).toBe('2026-10-16');
    expect(clinicCalendarDay(selectedDate)).toBe('2026-10-17');
    expect(clinicLocalAppointmentTime('2026-10-17', 9, 30).toISOString())
      .toBe('2026-10-17T08:30:00.000Z');
  });

  it('preserves the local calendar date when editing a UTC API timestamp', () => {
    const appointmentFromAPI = new Date('2026-10-16T23:20:00.000Z');
    expect(clinicCalendarDay(appointmentFromAPI)).toBe('2026-10-17');
    expect(clinicLocalAppointmentTime('2026-10-17', 0, 20).toISOString())
      .toBe(appointmentFromAPI.toISOString());
  });

  it('rejects invalid and rolled local date/time input', () => {
    expect(() => clinicLocalAppointmentTime('2026-02-30', 9, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 24, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 9, 60)).toThrow();
    expect(() => clinicCalendarDay(new Date(Number.NaN))).toThrow();
  });
});
