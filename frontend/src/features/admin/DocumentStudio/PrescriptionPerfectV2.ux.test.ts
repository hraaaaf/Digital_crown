import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const header = source('StudioHeader.tsx');
const prescription = source('Forms/PrescriptionAgenticStudioV1.tsx');
const drugRow = source('Forms/DrugRowV1.tsx');
const livePreview = source('LivePreview.tsx');

describe('Ordonnance Perfect V2 UX contract', () => {
  it('compacts only the ordonnance shell while preserving 44px clinical controls', () => {
    expect(header).toContain("const compactOrdonnance = activeTab === 'ordonnance'");
    expect(header).toContain('id="document-studio-author"');
    expect(header).toContain('id="document-studio-date"');
    expect(header).toContain('min-h-11');
    expect(header).toContain("activeTab === 'honoraires'");
  });

  it('keeps the ordonnance header in normal flow so it cannot cover prescription content', () => {
    expect(header).toContain('compactOrdonnance ? "relative z-20" : "sticky top-0 z-[60]"');
  });

  it('keeps legacy quick-entry hidden from the active V1 clinical path', () => {
    expect(drugRow).toContain('[data-ordonnance-quick-entry] { display: none !important; }');
    expect(prescription).not.toContain('QuickEntryBar');
  });

  it('does not expose legacy protocol presets in the V1 prescription flow', () => {
    expect(prescription).not.toContain('data-ordonnance-protocol-chips');
    expect(prescription).not.toContain('DEFAULT_MOROCCO_PRESETS.map');
    expect(prescription).not.toContain('applySystemProtocol');
    expect(prescription).toContain('Suggestion clinique bloquée');
  });

  it('keeps clinical automation explicitly fail-closed', () => {
    expect(prescription).toContain('Prescription Intelligence V1');
    expect(prescription).toContain('Recherche documentaire → présentation explicite → validation praticien');
    expect(prescription).toContain('data-clinical-rule-status="blocked"');
    expect(prescription).toContain('data-safety-status="blocked"');
    expect(prescription).toContain('Contrôle clinique automatique bloqué.');
    expect(prescription).not.toContain("api.post('/prescriptions/safety/check'");
    expect(prescription).toContain('min-h-11');
  });

  it('does not regress the responsive live preview back to a content-squeezing drawer', () => {
    expect(livePreview).toContain('document-studio-live-preview fixed inset-0');
    expect(livePreview).toContain('aria-modal="true"');
    expect(livePreview).not.toContain('fixed right-0 top-0');
  });
});
