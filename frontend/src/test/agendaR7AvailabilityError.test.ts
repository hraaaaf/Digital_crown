import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(
  path.join(process.cwd(), 'src/features/agenda/AgendaModal.tsx'),
  'utf8',
);

describe('Agenda R7 availability errors', () => {
  it('surfaces the authoritative backend availability reason', () => {
    expect(source).toContain("err?.response?.data?.detail");
    expect(source).toContain("Erreur lors de la sauvegarde du rendez-vous.");
  });
});
