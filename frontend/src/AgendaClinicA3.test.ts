import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('agenda clinic A3 practitioner availability', () => {
  it('renders practitioner hours, pauses and absences without changing the shared time axis', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(view).toContain("type SlotState = 'AVAILABLE' | 'GLOBAL_CLOSED' | 'PRACTITIONER_HOURS' | 'PAUSE' | 'LEAVE'");
    expect(view).toContain('getPractitionerSlotAvailability');
    expect(view).toContain('Cabinet fermé');
    expect(view).toContain('Hors horaires praticien');
    expect(view).toContain('Pause');
    expect(view).toContain('Absence');
    expect(view).toContain('data-testid="multi-practitioner-scroll"');
    expect(view).toContain('gridTemplateColumns: gridColumns');
  });

  it('keeps legacy practitioners on cabinet inheritance until an explicit override exists', () => {
    const panel = read('./features/admin/Settings/tabs/PractitionerAvailabilityPanel.tsx');

    expect(panel).toContain('Hérite du cabinet');
    expect(panel).toContain('disponibilité effective = cabinet ∩ praticien');
    expect(panel).toContain("api.put(`/agenda/practitioners/${selectedId}/settings`");
    expect(panel).toContain("api.delete(`/agenda/practitioners/${selectedId}/settings`");
    expect(panel).toContain("api.post(`/agenda/practitioners/${selectedId}/exceptions`");
  });

  // Regression guard for older Settings/browser harnesses that return {} on unknown GET endpoints.
  it('fails safe when legacy harnesses return non-array collection payloads', () => {
    const panel = read('./features/admin/Settings/tabs/PractitionerAvailabilityPanel.tsx');

    expect(panel).toContain('Array.isArray(response.data) ? response.data : []');
    expect(panel).toContain('Array.isArray(exceptionsResponse.data) ? exceptionsResponse.data : []');
    expect(panel).toContain('Aucun praticien assignable actif.');
  });

  it('passes the effective practitioner into every server-side availability gate', () => {
    const appointments = read('../../backend/routers/appointments.py');

    expect(appointments).toContain('practitioner_id=practitioner_id');
    expect(appointments).toContain('practitioner_id=effective_practitioner');
    expect(appointments).toContain('availability_error = validate_appointment_availability');
    expect(appointments).toContain('get_practitioner_day_availability');
    expect(appointments).toContain('models.SchedulingType.EXACT_TIME');
  });

  it('preserves the legacy NULL appointment global blocker contract', () => {
    const appointments = read('../../backend/routers/appointments.py');
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(appointments).toContain('models.Appointment.praticien_id.is_(None)');
    expect(view).toContain('bloque tous les praticiens');
  });
});
