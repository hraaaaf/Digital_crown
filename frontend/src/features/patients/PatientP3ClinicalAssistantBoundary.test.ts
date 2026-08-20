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

  it('keeps assistant output session-only until explicit practitioner validation', () => {
    expect(hub).toContain('Proposition à valider');
    expect(hub).toContain('Une proposition d’assistant ne devient jamais une conclusion sans cette action explicite.');
    expect(hub).toContain('const handleWizardComplete');
    expect(hub).toContain('setLastProposal({ text: proposalText');
    expect(hub).toContain('patientClinicalPersistence.createConclusion');
    expect(hub).toContain('Enregistrer la conclusion');

    const handlerStart = hub.indexOf('const handleWizardComplete');
    const handlerEnd = hub.indexOf('const completedSteps', handlerStart);
    const handler = hub.slice(handlerStart, handlerEnd);
    expect(handler).not.toContain('savePlan(');
    expect(handler).not.toContain('createConclusion(');
    expect(handler).not.toContain('/prescriptions');
    expect(handler).not.toContain('/accounting');
  });
});
