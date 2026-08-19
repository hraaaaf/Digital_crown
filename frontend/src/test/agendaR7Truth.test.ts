import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(
  path.join(process.cwd(), 'src/features/admin/Settings/tabs/AgendaTab.tsx'),
  'utf8',
);

describe('Settings R7 Agenda truth', () => {
  it('removes dead cabinet-wide agenda mode and ticket controls', () => {
    expect(source).not.toContain("Mode d'Agenda");
    expect(source).not.toContain("File d'attente (Tickets)");
    expect(source).not.toContain('Activer les tickets patients');
  });

  it('edits and persists a seven-day weekly schedule', () => {
    for (const key of ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']) {
      expect(source).toContain(`'${key}'`);
    }
    expect(source).toContain('weekly_schedule');
    expect(source).toContain("await api.put('/agenda/settings', settings)");
    expect(source).toContain('Modifications non enregistrées');
  });

  it('exposes real Agenda exception CRUD without browser prompts', () => {
    expect(source).toContain("api.get('/agenda/exceptions')");
    expect(source).toContain("api.post('/agenda/exceptions'");
    expect(source).toContain('api.delete(`/agenda/exceptions/${id}`)');
    expect(source).not.toContain('window.prompt');
    expect(source).not.toContain('window.confirm');
  });

  it('validates ranges before saving', () => {
    expect(source).toContain('validateWeek(settings.weekly_schedule)');
    expect(source).toContain('les plages matin et après-midi se chevauchent');
    expect(source).toContain('La date de fin doit être postérieure ou égale à la date de début.');
  });
});
