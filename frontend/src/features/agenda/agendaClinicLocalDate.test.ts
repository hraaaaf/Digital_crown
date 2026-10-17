import { afterEach, describe, expect, it, vi } from 'vitest';
import { clinicCalendarDay, clinicLocalAppointmentTime } from './agendaClinicLocalDate';

afterEach(() => vi.unstubAllEnvs());

describe('LOT07 P2 clinic calendar dates — date-only input is never UTC', () => {
  it('uses the Casablanca calendar day for creation near local midnight', () => {
    vi.stubEnv('TZ', 'Africa/Casablanca');
    const selectedDate = new Date(2026, 9, 17, 0, 20);
    expect(selectedDate.toISOString().slice(0, 10)).toBe('2026-10-16');
    expect(clinicCalendarDay(selectedDate)).toBe('2026-10-17');
    expect(clinicLocalAppointmentTime('2026-10-17', 9, 30).toISOString())
      .toBe('2026-10-17T08:30:00.000Z');
  });

  it('preserves the local date when editing an existing UTC timestamp', () => {
    vi.stubEnv('TZ', 'Africa/Casablanca');
    const appointmentFromAPI = new Date('2026-10-16T23:20:00.000Z');
    expect(clinicCalendarDay(appointmentFromAPI)).toBe('2026-10-17');
    expect(clinicLocalAppointmentTime('2026-10-17', 0, 20).toISOString())
      .toBe(appointmentFromAPI.toISOString());
  });

  it('also preserves day and exact clock time west of UTC', () => {
    vi.stubEnv('TZ', 'America/New_York');
    const when = clinicLocalAppointmentTime('2026-10-17', 0, 20);
    expect(clinicCalendarDay(when)).toBe('2026-10-17');
    expect(when.getHours()).toBe(0);
    expect(when.getMinutes()).toBe(20);
  });

  it('refuses invalid input instead of silently rolling dates forward', () => {
    vi.stubEnv('TZ', 'Africa/Casablanca');
    expect(() => clinicLocalAppointmentTime('2026-02-30', 9, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 24, 0)).toThrow();
    expect(() => clinicLocalAppointmentTime('2026-10-17', 9, 60)).toThrow();
    expect(() => clinicCalendarDay(new Date(Number.NaN))).toThrow();
  });
});
