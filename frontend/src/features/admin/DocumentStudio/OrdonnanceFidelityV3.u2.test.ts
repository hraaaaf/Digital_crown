import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const prescription = source('Forms/PrescriptionAgenticStudio.tsx');
const quickEntry = source('Forms/QuickEntryBar.tsx');

describe('Ordonnance Fidelity V3 U2 clinical density', () => {
  it('marks the U2 density surface and reduces wrapper spacing', () => {
    expect(prescription).toContain('data-ordonnance-density="u2"');
    expect(prescription).toContain('prescription-r3-safety-orchestrated space-y-2');
    expect(prescription).toContain('data-ordonnance-density-context');
  });

  it('compacts legacy vertical rhythm without shrinking the add-line action below 44px', () => {
    expect(prescription).toContain('margin-top: 0.75rem !important;');
    expect(prescription).toContain('margin-top: 0.625rem !important;');
    expect(prescription).toContain('button[class~="py-5"][class~="border-dashed"]');
    expect(prescription).toContain('min-height: 44px;');
  });

  it('keeps protocol and context actions touch-safe', () => {
    expect(prescription.match(/min-h-11/g)?.length ?? 0).toBeGreaterThanOrEqual(3);
    expect(quickEntry).toContain('min-h-14');
    expect(quickEntry.match(/min-h-11/g)?.length ?? 0).toBeGreaterThanOrEqual(3);
  });

  it('does not introduce a local Ordonnance theme or hard-coded hex palette', () => {
    expect(prescription).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(prescription).not.toContain('data-theme=');
  });
});
