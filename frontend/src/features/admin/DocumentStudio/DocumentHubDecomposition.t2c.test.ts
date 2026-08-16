import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const hub = readFileSync(new URL('../DocumentHub.tsx', import.meta.url), 'utf8');
const navigation = readFileSync(new URL('./useDocumentHubNavigation.ts', import.meta.url), 'utf8');
const patient = readFileSync(new URL('./useDocumentHubPatient.ts', import.meta.url), 'utf8');
const content = readFileSync(new URL('./DocumentHubContent.tsx', import.meta.url), 'utf8');
const preview = readFileSync(new URL('./DocumentHubPreview.tsx', import.meta.url), 'utf8');
const dialogs = readFileSync(new URL('./DocumentHubDialogs.tsx', import.meta.url), 'utf8');

describe('Document Studio T2-C shell decomposition', () => {
  it('keeps DocumentHub as orchestration and shell composition instead of owning navigation plumbing', () => {
    expect(hub).toContain("import { useDocumentHubNavigation } from './DocumentStudio/useDocumentHubNavigation'");
    expect(hub).toContain("import { useDocumentHubPatient } from './DocumentStudio/useDocumentHubPatient'");
    expect(hub).toContain("import { DocumentHubContent } from './DocumentStudio/DocumentHubContent'");
    expect(hub).toContain("import { DocumentHubPreview } from './DocumentStudio/DocumentHubPreview'");
    expect(hub).toContain("import { DocumentHubDialogs } from './DocumentStudio/DocumentHubDialogs'");
    expect(hub).not.toContain('useSearchParams');
    expect(hub).not.toContain('shouldGuardDocumentTabTransition');
    expect(hub).not.toContain('api.get(`/patients/${patientId}`)');
  });

  it('centralizes canonical URL and dirty-transition behavior in the navigation boundary', () => {
    expect(navigation).toContain('useSearchParams');
    expect(navigation).toContain('shouldGuardDocumentTabTransition');
    expect(navigation).toContain("activeTab === 'devis' && newTab === 'honoraires'");
    expect(navigation).toContain("window.addEventListener('beforeunload', handler)");
    expect(navigation).toContain("nextParams.set('documentTab', activeTab)");
  });

  it('keeps patient loading in its dedicated session boundary', () => {
    expect(patient).toContain('useDocumentHubPatient');
    expect(patient).toContain('api.get(`/patients/${patientId}`)');
    expect(patient).toContain('setPatientDetails(null)');
  });

  it('keeps all seven domain pages behind the content boundary', () => {
    expect(content).toContain('TreatmentPlanStudio');
    expect(content).toContain('PrescriptionAgenticStudio');
    expect(content).toContain('CertificateForm');
    expect(content).toContain('AccountingStudio');
    expect(content).toContain('InstallmentStudio');
    expect(content).toContain('LibreForm');
    expect(content).toContain("activeTab === 'devis' || activeTab === 'honoraires'");
  });

  it('keeps preview freshness and dialogs outside the root shell', () => {
    expect(preview).toContain('useDocumentPreviewController');
    expect(preview).toContain('pdfUrl={stale ? null : pdfUrl}');
    expect(dialogs).toContain('showDiscardDraft');
    expect(dialogs).toContain('showDuplicate');
  });
});
