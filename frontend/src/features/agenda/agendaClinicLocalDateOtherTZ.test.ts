import { describe, expect, it } from 'vitest';
import { clinicAppointmentWallTime, clinicAppointmentFormFields } from './agendaClinicLocalDate';

describe('LOT07 P2 — canonical wall time in any browser/runner timezone', () => {
  it('sends identical business time for Casablanca and New York processes', () => {
    expect(clinicAppointmentWallTime('2026-10-17', 9, 30)).toBe('2026-10-17T09:30:00');
    expect(clinicAppointmentFormFields('2026-10-17T09:30:00')).toEqual({date:'2026-10-17',time:'09:30'});
  });
});
