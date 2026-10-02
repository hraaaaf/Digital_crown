import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (file: string) => readFileSync(resolve(process.cwd(), file), 'utf8');
const drugRow = read('src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx');
const contextualChoice = read('src/features/admin/DocumentStudio/Forms/PrescriptionContextualChoice.tsx');

describe('Ordonnance Fidelity V3.1 prescription composer', () => {
  it('renders the four structured controls with one primary posology text source', () => {
    expect(drugRow).toContain('data-ordonnance-prescription-composer');
    for (const label of ['Prise', 'Rythme', 'Durée ou limite', 'Moment ou condition']) {
      expect(drugRow).toContain(`ariaLabel="${label}"`);
    }
    expect(drugRow).toContain('Posologie complète');
    expect(drugRow).not.toContain('Phrase persistée');
  });

  it('keeps free text as a fallback instead of changing the backend contract', () => {
    expect(drugRow).toContain('aria-label="Posologie en texte libre"');
    expect(drugRow).toContain("onUpdateDrug(drug.id, 'posologie'");
  });

  it('keeps every structured selector touch-safe', () => {
    expect(contextualChoice).toContain('data-composer-field={dataField}');
    expect(contextualChoice).toContain('min-h-11');
    expect((drugRow.match(/<PrescriptionContextualChoice/g) || []).length).toBeGreaterThanOrEqual(4);
  });

  it('inherits the active app theme with no local palette', () => {
    const combined = `${drugRow}\n${contextualChoice}`;
    for (const tokenClass of ['bg-glass-bg', 'bg-input-field', 'border-border-main', 'text-text-main', 'text-text-muted']) {
      expect(combined).toContain(tokenClass);
    }
    expect(combined).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(combined).not.toContain('data-theme=');
  });
});
