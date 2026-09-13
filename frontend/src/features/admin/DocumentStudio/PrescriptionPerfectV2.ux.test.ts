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
  it('compacts only the ordonnance shell while preserving 44px clinical controls', () => {
    expect(header).toContain("const compactOrdonnance = activeTab === 'ordonnance'");
    expect(header).toContain('id="document-studio-author"');
    expect(header).toContain('id="document-studio-date"');
    expect(header).toContain('min-h-11');
    expect(header).toContain("activeTab === 'honoraires'");
  });

  it('keeps deterministic prescription safety and established clinical copy visible', () => {
    expect(prescription).toContain('Contexte patient');
    expect(prescription).toContain('Données du dossier et vérifications déterministes utilisées pour l’ordonnance en cours.');
    expect(prescription).toContain('renseignée');
    expect(prescription).toContain('data-safety-status={safetyStatus}');
    expect(prescription).toContain("api.post('/prescriptions/safety/check'");
    expect(prescription).toContain('dark:bg-slate-900/45');
    expect(prescription).toContain('Mes protocoles');
    expect(prescription).toContain('Actualiser le contexte');
    expect(prescription).toContain('min-h-11');
  });

  it('does not regress the responsive live preview back to a content-squeezing drawer', () => {
    expect(livePreview).toContain('document-studio-live-preview fixed inset-0');
    expect(livePreview).toContain('aria-modal="true"');
    expect(livePreview).not.toContain('fixed right-0 top-0');
  });
});
