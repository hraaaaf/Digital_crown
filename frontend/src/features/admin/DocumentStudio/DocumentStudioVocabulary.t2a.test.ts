import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_STUDIO_LABELS,
  DOCUMENT_STUDIO_PREVIEW_TITLES,
  DOCUMENT_STUDIO_TABS,
  isCertifiableDocumentStudioTab,
} from './DocumentStudioVocabulary';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);
const tabsSource = source('StudioTabs.tsx');
const headerSource = source('StudioHeader.tsx');
const footerSource = source('StudioFooter.tsx');
const navigationPolicySource = source('DocumentTabNavigationPolicy.ts');

describe('Document Studio canonical product vocabulary', () => {
  it('exposes exactly the six document-producing surfaces', () => {
    expect(DOCUMENT_STUDIO_TABS).toEqual([
      'ordonnance',
      'certificat',
      'devis',
      'honoraires',
      'echeancier',
      'libre',
    ]);
    expect(Object.keys(DOCUMENT_STUDIO_LABELS)).toEqual(DOCUMENT_STUDIO_TABS);
    expect(DOCUMENT_STUDIO_LABELS).not.toHaveProperty('ai');
    expect(DOCUMENT_STUDIO_LABELS).not.toHaveProperty('plan');
  });

  it('rejects clinical and dormant AI routes from the document tab parser', () => {
    expect(isCertifiableDocumentStudioTab('ordonnance')).toBe(true);
    expect(isCertifiableDocumentStudioTab('plan')).toBe(false);
    expect(isCertifiableDocumentStudioTab('ai')).toBe(false);
    expect(isCertifiableDocumentStudioTab(null)).toBe(false);
  });

  it('keeps navigation and preview naming aligned to the document-only language', () => {
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES.echeancier).toBe('Suivi Paiement');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES).not.toHaveProperty('ai');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES).not.toHaveProperty('plan');
  });

  it('keeps presentation and navigation types on the canonical six-tab vocabulary', () => {
    for (const shellSource of [tabsSource, headerSource, footerSource]) {
      expect(shellSource).not.toContain("import('../DocumentHub').HubDocumentType");
      expect(shellSource).toContain('DocumentStudioVocabulary');
    }
    expect(headerSource).not.toContain("| 'ai'");
    expect(headerSource).not.toContain("activeTab === 'ai'");
    expect(navigationPolicySource).toContain('CertifiableDocumentStudioTab');
    expect(navigationPolicySource).not.toContain("case 'plan'");
  });
});