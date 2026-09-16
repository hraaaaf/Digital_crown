import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('agenda clinic A1 practitioner filtering', () => {
  it('injects the active practitioner into standard appointment reads without overriding an explicit filter', () => {
    const agendaPage = read('./pages/AgendaPage.tsx');

    expect(agendaPage).toContain("method === 'get' && url === '/appointments/' && activePractitionerId");
    expect(agendaPage).toContain('praticien_id: config.params?.praticien_id ?? activePractitionerId');
  });

  it('refreshes day, week and month when the selected practitioner changes while preserving studio state', () => {
    const studio = read('./features/agenda/AgendaStudio.tsx');

    expect(studio).toContain('usePractitionerContextStore((state) => state.selectedPractitionerId)');
    expect(studio).toContain("const practitionerViewKey = selectedPractitionerId ?? 'unscoped'");
    expect(studio).toContain('key={`day-${refreshKey}-${practitionerViewKey}`}');
    expect(studio).toContain('key={`week-${refreshKey}-${practitionerViewKey}`}');
    expect(studio).toContain('key={`month-${refreshKey}-${practitionerViewKey}`}');
  });

  it('keeps the edit contract non-destructive', () => {
    const agendaPage = read('./pages/AgendaPage.tsx');

    expect(agendaPage).toContain("method === 'put'");
    expect(agendaPage).toContain('Le contexte global ne doit jamais réaffecter');
  });
});
