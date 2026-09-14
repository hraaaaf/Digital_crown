import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const drugRow = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/Forms/DrugRow.tsx'),
  'utf8',
);

describe('Ordonnance Fidelity V3 U4 medication cards', () => {
  it('exposes a semantic medication card with strong clinical identity', () => {
    expect(drugRow).toContain('data-ordonnance-drug-card');
    expect(drugRow).toContain('Médicament ${String(idx + 1).padStart');
    expect(drugRow).toContain('Posologie');
    expect(drugRow).toContain('Dose');
  });

  it('inherits semantic theme surfaces instead of introducing a local palette', () => {
    for (const tokenClass of [
      'bg-card',
      'bg-input-field',
      'text-text-main',
      'text-text-muted',
      'border-border-main',
    ]) {
      expect(drugRow).toContain(tokenClass);
    }
    expect(drugRow).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(drugRow).not.toContain('data-theme=');
  });

  it('keeps primary medication controls touch-safe', () => {
    expect(drugRow.match(/h-11 w-11/g)?.length ?? 0).toBeGreaterThanOrEqual(5);
    expect(drugRow.match(/min-h-11/g)?.length ?? 0).toBeGreaterThanOrEqual(5);
  });

  it('preserves medication behavior callbacks', () => {
    for (const callback of [
      'onToggleType',
      'onSearch',
      'onApplySuggestion',
      'onFormeOpen',
      'onUpdateDrug',
      'onMove',
      'onRemoveDrug',
    ]) {
      expect(drugRow).toContain(callback);
    }
  });
});
