import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const drugRow = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx'),
  'utf8',
);

describe('Ordonnance Fidelity V3.1 prescription composer', () => {
  it('renders the four structured controls and persisted phrase', () => {
    expect(drugRow).toContain('data-ordonnance-prescription-composer');
    for (const field of ['amount', 'frequency', 'constraint', 'context']) {
      expect(drugRow).toContain(`data-composer-field="${field}"`);
    }
    expect(drugRow).toContain('Phrase persistée');
    expect(drugRow).toContain('Prescription structurée');
  });

  it('keeps free text as a fallback instead of changing the backend contract', () => {
    expect(drugRow).toContain('Texte libre');
    expect(drugRow).toContain('aria-label="Posologie en texte libre"');
    expect(drugRow).toContain("onUpdateDrug(drug.id, 'posologie'");
  });

  it('keeps all four structured selectors touch-safe', () => {
    const composerStart = drugRow.indexOf('data-ordonnance-prescription-composer');
    const composerEnd = drugRow.indexOf('aria-label="Posologie en texte libre"', composerStart);
    const composerSource = drugRow.slice(composerStart, composerEnd);
    expect(composerSource.match(/min-h-11/g)?.length ?? 0).toBeGreaterThanOrEqual(4);
  });

  it('inherits the active app theme with no local palette', () => {
    const composerStart = drugRow.indexOf('data-ordonnance-prescription-composer');
    const composerEnd = drugRow.indexOf('aria-label="Posologie en texte libre"', composerStart);
    const composerSource = drugRow.slice(composerStart, composerEnd);
    for (const tokenClass of ['bg-glass-bg', 'bg-input-field', 'border-border-main', 'text-text-main', 'text-text-muted']) {
      expect(composerSource).toContain(tokenClass);
    }
    expect(composerSource).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(composerSource).not.toContain('data-theme=');
  });
});
