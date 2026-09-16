import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('agenda clinic A2 synchronized multi-practitioner grid', () => {
  it('uses a daily multi-practitioner range and day-by-day navigation', () => {
    const studio = read('./features/agenda/AgendaStudio.tsx');

    expect(studio).toContain("viewMode === 'day' || viewMode === 'multi'");
    expect(studio).toContain('start.setHours(0, 0, 0, 0)');
    expect(studio).toContain('end.setHours(23, 59, 59, 999)');
    expect(studio).toContain('<MultiPractitionerTimelineView');
  });

  it('keeps a common time axis, practitioner lanes and explicit legacy blockers', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(view).toContain('const TIME_AXIS_WIDTH = 68');
    expect(view).toContain('const LANE_MIN_WIDTH = 220');
    expect(view).toContain('gridTemplateColumns: gridColumns');
    expect(view).toContain('Non assigné ·');
    expect(view).toContain('bloque tous les praticiens');
    expect(view).toContain('data-testid="multi-practitioner-scroll"');
  });

  it('binds the clicked practitioner before opening create, and never on edit PUTs', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(view).toContain("url === '/appointments/check-conflicts'");
    expect(view).toContain('praticien_id: config.params?.praticien_id ?? practitionerId');
    expect(view).toContain("method === 'post' && url === '/appointments/'");
    expect(view).toContain('addPractitionerToPayload(config.data, practitionerId)');
    expect(view).toContain('installCreateInterceptor(dentist.dentist_id);');
    expect(view.indexOf('installCreateInterceptor(dentist.dentist_id);')).toBeLessThan(view.indexOf('setIsModalOpen(true);'));
    expect(view).toContain('const openEdit =');
    expect(view).toContain('clearCreateInterceptor();');
    expect(view).not.toContain("method === 'put' && url === '/appointments/'");
  });

  it('preserves flexible appointments without inventing an exact hour', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(view).toContain("appointment.scheduling_type === 'MORNING'");
    expect(view).toContain("appointment.scheduling_type === 'AFTERNOON'");
    expect(view).toContain("appointment.scheduling_type === 'FULL_DAY'");
    expect(view).toContain('Rendez-vous flexibles non assignés');
  });
});
