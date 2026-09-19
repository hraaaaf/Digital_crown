import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();

describe('Ortho F4 UI contract', () => {
  it('mounts cockpit before F3 and generic PatientJourney', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/patients/PatientDetailsInner.tsx'), 'utf8');
    const cockpit = file.indexOf('<OrthoCockpitPanel');
    const compare = file.indexOf('<OrthoLongitudinalComparePanel');
    const journey = file.indexOf('<PatientJourney');
    expect(cockpit).toBeGreaterThan(-1);
    expect(compare).toBeGreaterThan(cockpit);
    expect(journey).toBeGreaterThan(compare);
  });

  it('keeps next control and real appointment explicitly distinct', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoCockpitPanel.tsx'), 'utf8');
    expect(file).toContain('Contrôle prévu');
    expect(file).toContain('RDV réel');
    expect(file).toContain('Aucun rendez-vous futur enregistré');
  });

  it('keeps F4 clinically neutral and source-oriented', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoCockpitPanel.tsx'), 'utf8').toLowerCase();
    for (const forbidden of ['score de progression', 'succès thérapeutique', 'échec thérapeutique', 'amélioration automatique', 'aggravation automatique']) {
      expect(file).not.toContain(forbidden);
    }
    expect(file).toContain('voir comparaison');
    expect(file).toContain("tab: 'radiology'");
  });

  it('uses a compact responsive grid without horizontal scrolling', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoCockpitPanel.tsx'), 'utf8');
    expect(file).toContain('md:grid-cols-3');
    expect(file).not.toContain('overflow-x-auto');
    expect(file).toContain('data-ortho-f4-cockpit');
  });
});
