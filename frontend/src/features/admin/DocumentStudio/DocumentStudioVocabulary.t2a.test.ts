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
  it('exposes exactly the seven certifiable P1→P7 surfaces', () => {
    expect(DOCUMENT_STUDIO_TABS).toEqual([
      'ordonnance',
      'certificat',
      'devis',
      'honoraires',
      'echeancier',
      'libre',
      'plan',
    ]);
    expect(Object.keys(DOCUMENT_STUDIO_LABELS)).toEqual(DOCUMENT_STUDIO_TABS);
    expect(DOCUMENT_STUDIO_LABELS).not.toHaveProperty('ai');
  });

  it('rejects the dormant ai route from the certifiable tab parser', () => {
    expect(isCertifiableDocumentStudioTab('ordonnance')).toBe(true);
    expect(isCertifiableDocumentStudioTab('plan')).toBe(true);
    expect(isCertifiableDocumentStudioTab('ai')).toBe(false);
    expect(isCertifiableDocumentStudioTab(null)).toBe(false);
  });

  it('keeps navigation and preview naming aligned to the canonical product language', () => {
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES.plan).toBe('Compagnon Diagnostique');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES.echeancier).toBe('Suivi Paiement');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES).not.toHaveProperty('ai');
  });

  it('keeps presentation and navigation types on the canonical P1→P7 vocabulary', () => {
    for (const shellSource of [tabsSource, headerSource, footerSource]) {
      expect(shellSource).not.toContain("import('../DocumentHub').HubDocumentType");
      expect(shellSource).toContain('DocumentStudioVocabulary');
    }
    expect(headerSource).not.toContain("| 'ai'");
    expect(headerSource).not.toContain("activeTab === 'ai'");
    expect(navigationPolicySource).toContain('CertifiableDocumentStudioTab');
    expect(navigationPolicySource).not.toContain("| 'ai'");
  });
});