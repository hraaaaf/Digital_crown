import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (name: string) => readFileSync(
  resolve(process.cwd(), `src/features/patients/components/wizards/${name}.tsx`),
  'utf8',
);

const specialized = [
  'AssistantGeneral',
  'AssistantParo',
  'AssistantEndo',
  'AssistantChirurgie',
  'AssistantProthese',
  'AssistantPedo',
  'AssistantOrtho',
  'AssistantATM',
  'AssistantPatho',
];

const hub = readFileSync(
  resolve(process.cwd(), 'src/features/patients/components/ClinicalHub.tsx'),
  'utf8',
);

const complete = read('AssistantExamenComplet');

describe('P3 clinical assistant authority boundary', () => {
  it.each(specialized)('%s returns a proposal without treatment-plan steps', (name) => {
    const source = read(name);
    expect(source).toContain('onComplete(summary, [])');
    expect(source).not.toContain('/prescriptions');
    expect(source).not.toContain('/accounting');
    expect(source).not.toContain('/master-plan');
  });

  it('keeps the complete examination questionnaire non-authoritative', () => {
    expect(complete).toContain('steps: [], next: null');
    expect(complete).toContain('ne pose pas automatiquement de diagnostic');
    expect(complete).toContain('décision du praticien');
  });

  it('keeps assistant output session-only in ClinicalHub', () => {
    expect(hub).toContain('Assistant output is session-only until explicitly validated by the practitioner.');
    expect(hub).toContain('Proposition clinique à valider');
    expect(hub).toContain('const handleWizardComplete');
    expect(hub).toContain('setLastDiagnosis(proposal)');
    expect(hub).not.toContain('savePlan(_steps');
    expect(hub).not.toContain('savePlan(steps');
  });
});
