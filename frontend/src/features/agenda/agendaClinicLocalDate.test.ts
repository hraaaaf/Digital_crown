import { describe, expect, it } from 'vitest';
import { clinicCalendarDay, clinicAppointmentWallTime, clinicAppointmentFormFields } from './agendaClinicLocalDate';

describe('LOT07 07-A — CABINET WALL-CLOCK, backend naive datetime contract', () => {
  it('preserves selected calendar day at local midnight', () => {
    expect(clinicCalendarDay(new Date(2026, 9, 17, 0, 20))).toBe('2026-10-17');
  });

  it('serializes a cabinet appointment as naive ISO without Z or browser offset', () => {
    expect(clinicAppointmentWallTime('2026-10-17', 9, 30)).toBe('2026-10-17T09:30:00');
    expect(clinicAppointmentWallTime('2026-10-17', 0, 20)).toBe('2026-10-17T00:20:00');
  });

  it('reads backend values without converting wall clock in the browser', () => {
    expect(clinicAppointmentFormFields('2026-10-17T09:30:00')).toEqual({date:'2026-10-17',time:'09:30'});
    expect(clinicAppointmentFormFields('2026-10-17T09:30:00.000')).toEqual({date:'2026-10-17',time:'09:30'});
    // Backend currently strips any supplied timezone rather than converting.
    expect(clinicAppointmentFormFields('2026-10-17T09:30:00+01:00')).toEqual({date:'2026-10-17',time:'09:30'});
  });

  it('rejects invalid dates and times without DST/browser dependence', () => {
    expect(() => clinicAppointmentWallTime('2026-02-30', 9, 0)).toThrow();
    expect(() => clinicAppointmentWallTime('2026-13-01', 9, 0)).toThrow();
    expect(() => clinicAppointmentWallTime('2026-10-17', 24, 0)).toThrow();
    expect(() => clinicAppointmentWallTime('2026-10-17', 9, 60)).toThrow();
    expect(() => clinicAppointmentFormFields('2026-10-17T25:00:00')).toThrow();
    expect(() => clinicCalendarDay(new Date(Number.NaN))).toThrow();
  });
});
