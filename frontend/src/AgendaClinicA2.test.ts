import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('agenda clinic A2 synchronized multi-practitioner grid', () => {
  it('uses a daily multi-practitioner range and day-by-day navigation', () => {
    const studio = read('./features/agenda/AgendaStudio.tsx');

    expect(studio).toContain("viewMode === 'day' || viewMode === 'multi'");
    expect(studio).toContain('const day = clinicCalendarDay(selectedDate)');
    expect(studio).toContain('start_date: `${day}T00:00:00`');
    expect(studio).toContain('end_date: `${day}T23:59:59.999999`');
    expect(studio).not.toContain('start.toISOString()');
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

  it('sends the clicked provider explicitly with both preflight and write, never via a global interceptor', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');
    const modal = read('./features/agenda/AgendaModal.tsx');
    expect(view).toContain('setModalPractitioner({ id: dentist.dentist_id, name: dentist.dentist_name })');
    expect(view).toContain('initialPractitionerId={modalPractitioner?.id}');
    expect(view).not.toContain('api.interceptors.request');
    expect(view).not.toContain('installCreateInterceptor');
    expect(modal).toContain('praticien_id: practitionerId');
    expect(modal).toContain('resource_id: resourceId');
    expect(modal).toContain('const submitInProgress = useRef(false)');
  });

  it('reads Day/Week/Month and header with cabinet day bounds rather than browser UTC instants', () => {
    const paths=[
      './features/agenda/DailyView.tsx',
      './features/agenda/WeeklyView.tsx',
      './features/agenda/MonthlyView.tsx',
      './features/clinic/ClinicPractitionerBar.tsx',
    ];
    for(const path of paths){
      const source=read(path);
      expect(source).toContain('clinicCalendarDay(');
      expect(source).toContain('T00:00:00');
      expect(source).toContain('T23:59:59.999999');
      expect(source).not.toContain('start.toISOString()');
      expect(source).not.toContain('end.toISOString()');
    }
  });

  it('preserves flexible appointments without inventing an exact hour', () => {
    const view = read('./features/agenda/MultiPractitionerTimelineView.tsx');

    expect(view).toContain("appointment.scheduling_type === 'MORNING'");
    expect(view).toContain("appointment.scheduling_type === 'AFTERNOON'");
    expect(view).toContain("appointment.scheduling_type === 'FULL_DAY'");
    expect(view).toContain('Rendez-vous flexibles non assignés');
  });
});
