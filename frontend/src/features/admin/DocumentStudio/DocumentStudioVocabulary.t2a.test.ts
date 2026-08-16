import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_STUDIO_LABELS,
  DOCUMENT_STUDIO_PREVIEW_TITLES,
  DOCUMENT_STUDIO_TABS,
  isCertifiableDocumentStudioTab,
} from './DocumentStudioVocabulary';

const tabsSource = readFileSync(new URL('./StudioTabs.tsx', import.meta.url), 'utf8');
const headerSource = readFileSync(new URL('./StudioHeader.tsx', import.meta.url), 'utf8');
const footerSource = readFileSync(new URL('./StudioFooter.tsx', import.meta.url), 'utf8');

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

  it('keeps presentation shell components decoupled from the DocumentHub monolith', () => {
    for (const source of [tabsSource, headerSource, footerSource]) {
      expect(source).not.toContain("import('../DocumentHub').HubDocumentType");
      expect(source).toContain('DocumentStudioVocabulary');
    }
  });
});
