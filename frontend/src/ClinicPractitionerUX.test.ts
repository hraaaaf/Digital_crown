import { readFileSync } from 'node:fs';
import { beforeEach, describe, expect, it } from 'vitest';
import { usePractitionerContextStore } from './features/clinic/practitionerContext';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('clinic practitioner context', () => {
  beforeEach(() => {
    usePractitionerContextStore.getState().resetPractitioners();
  });

  it('preserves the selected practitioner while the refreshed team still contains it', () => {
    const store = usePractitionerContextStore.getState();
    store.setPractitioners([
      { id: 1, name: 'Dr Lina Alaoui' },
      { id: 2, name: 'Dr Youssef Benali' },
    ]);
    usePractitionerContextStore.getState().selectPractitioner({ id: 2, name: 'Dr Youssef Benali' });

    usePractitionerContextStore.getState().setPractitioners([
      { id: 1, name: 'Dr Lina Alaoui', appointmentCount: 1 },
      { id: 2, name: 'Dr Youssef Benali', appointmentCount: 3 },
    ]);

    expect(usePractitionerContextStore.getState().selectedPractitionerId).toBe(2);
    expect(usePractitionerContextStore.getState().selectedPractitionerName).toBe('Dr Youssef Benali');
  });

  it('falls back to the first valid practitioner when the previous selection disappears', () => {
    const store = usePractitionerContextStore.getState();
    store.setPractitioners([{ id: 8, name: 'Dr A' }, { id: 9, name: 'Dr B' }]);
    usePractitionerContextStore.getState().selectPractitioner({ id: 9, name: 'Dr B' });
    usePractitionerContextStore.getState().setPractitioners([{ id: 8, name: 'Dr A' }]);

    expect(usePractitionerContextStore.getState().selectedPractitionerId).toBe(8);
  });

  it('keeps the Agenda write contract explicit and non-destructive', () => {
    const agenda = read('./pages/AgendaPage.tsx');
    expect(agenda).toContain("url === '/appointments/'");
    expect(agenda).toContain("url === '/appointments/check-conflicts'");
    expect(agenda).toContain("url === '/appointments/bulk'");
    expect(agenda).toContain('appointment.praticien_id ?? activePractitionerId');
    expect(agenda).toContain('Le contexte global ne doit jamais réaffecter');
    expect(agenda).toContain("method === 'put'");
    expect(agenda).toContain('return config;');
  });

  it('keeps the context visible on the three P1 surfaces', () => {
    const layout = read('./components/Layout/MainLayout.tsx');
    expect(layout).toContain("['/dashboard', '/agenda', '/settings']");
    expect(layout).toContain('<ClinicPractitionerBar />');
  });
});
