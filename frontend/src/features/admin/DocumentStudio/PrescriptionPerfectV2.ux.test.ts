import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const header = source('StudioHeader.tsx');
const prescription = source('Forms/PrescriptionAgenticStudio.tsx');
const livePreview = source('LivePreview.tsx');

describe('Ordonnance Perfect V2 UX contract', () => {
  it('compacts only the ordonnance shell while preserving the clinical author and date controls', () => {
    expect(header).toContain("const compactOrdonnance = activeTab === 'ordonnance'");
    expect(header).toContain('id="document-studio-author"');
    expect(header).toContain('id="document-studio-date"');
    expect(header).toContain("activeTab === 'honoraires'");
  });

  it('keeps deterministic prescription safety visible while reducing visual weight', () => {
    expect(prescription).toContain('Sécurité clinique');
    expect(prescription).toContain('data-safety-status={safetyStatus}');
    expect(prescription).toContain("api.post('/prescriptions/safety/check'");
    expect(prescription).toContain('dark:bg-slate-900/45');
    expect(prescription).toContain('Protocoles');
    expect(prescription).toContain('Actualiser');
  });

  it('does not regress the responsive live preview back to a content-squeezing drawer', () => {
    expect(livePreview).toContain('document-studio-live-preview fixed inset-0');
    expect(livePreview).toContain('aria-modal="true"');
    expect(livePreview).not.toContain('fixed right-0 top-0');
  });
});
