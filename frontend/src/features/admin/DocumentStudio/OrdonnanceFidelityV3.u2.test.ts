import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const prescription = source('Forms/PrescriptionAgenticStudioV1.tsx');
const drugRow = source('Forms/DrugRowV1.tsx');

describe('Ordonnance Fidelity V3 U2 clinical density', () => {
  it('keeps the V1 ordonnance surface compact', () => {
    expect(prescription).toContain('data-prescription-intelligence-studio="v1"');
    expect(prescription).toContain('className="space-y-3"');
    expect(prescription).toContain('sm:p-4');
  });

  it('keeps add-line and medication actions touch-safe', () => {
    expect(prescription).toContain('min-h-11');
    expect(drugRow.match(/h-11 w-11/g)?.length ?? 0).toBeGreaterThanOrEqual(5);
    expect(drugRow.match(/min-h-11/g)?.length ?? 0).toBeGreaterThanOrEqual(5);
  });

  it('does not expose legacy quick-entry or protocol chips in the active V1 studio', () => {
    expect(prescription).not.toContain('data-ordonnance-protocol-chips');
    expect(prescription).not.toContain('DEFAULT_MOROCCO_PRESETS.map');
    expect(prescription).not.toContain('PrescriptionAgenticStudioLegacy');
    expect(drugRow).toContain('[data-ordonnance-quick-entry] { display: none !important; }');
  });

  it('does not introduce a local Ordonnance theme or hard-coded hex palette', () => {
    expect(prescription).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(prescription).not.toContain('data-theme=');
    expect(drugRow).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
