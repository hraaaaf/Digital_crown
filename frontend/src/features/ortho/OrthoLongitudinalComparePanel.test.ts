import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();

describe('Ortho F3 UI contract', () => {
  it('mounts the longitudinal comparison before the generic PatientJourney', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/patients/PatientDetailsInner.tsx'), 'utf8');
    const compare = file.indexOf('<OrthoLongitudinalComparePanel');
    const journey = file.indexOf('<PatientJourney');
    expect(compare).toBeGreaterThan(-1);
    expect(journey).toBeGreaterThan(-1);
    expect(compare).toBeLessThan(journey);
  });

  it('keeps comparison copy clinically neutral', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoLongitudinalComparePanel.tsx'), 'utf8').toLowerCase();
    for (const forbidden of ['amélioration automatique', 'aggravation automatique', 'succès thérapeutique', 'échec thérapeutique']) {
      expect(file).not.toContain(forbidden);
    }
    expect(file).toContain('variation numérique');
    expect(file).toContain('interprétation clinique par le praticien');
  });

  it('keeps mobile comparison free of horizontal table scrolling', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoLongitudinalComparePanel.tsx'), 'utf8');
    expect(file).toContain('sm:hidden');
    expect(file).toContain('hidden overflow-hidden');
    expect(file).not.toContain('overflow-x-auto');
  });
});
