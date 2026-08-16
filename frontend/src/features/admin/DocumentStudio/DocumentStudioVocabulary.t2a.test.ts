import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_STUDIO_LABELS,
  DOCUMENT_STUDIO_PREVIEW_TITLES,
} from './DocumentStudioVocabulary';

describe('Document Studio canonical product vocabulary', () => {
  it('exposes exactly the seven certifiable P1→P7 surfaces', () => {
    expect(Object.keys(DOCUMENT_STUDIO_LABELS)).toEqual([
      'ordonnance',
      'certificat',
      'devis',
      'honoraires',
      'echeancier',
      'libre',
      'plan',
    ]);
    expect(DOCUMENT_STUDIO_LABELS).not.toHaveProperty('ai');
  });

  it('keeps navigation and preview naming aligned to the canonical product language', () => {
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES.plan).toBe('Compagnon Diagnostique');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES.echeancier).toBe('Suivi Paiement');
    expect(DOCUMENT_STUDIO_PREVIEW_TITLES).not.toHaveProperty('ai');
  });
});
