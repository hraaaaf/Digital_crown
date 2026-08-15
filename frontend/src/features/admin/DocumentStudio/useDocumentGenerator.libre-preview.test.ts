import { describe, expect, it } from 'vitest';

import {
  shouldSkipInvalidLibrePreview,
} from './useDocumentGenerator';

const baseParams = {
  patientId: '1',
  patientDetails: null,
  activeTab: 'libre',
  drugs: [],
  certifType: '',
  certifDays: 0,
  certifStartDate: '',
  certifCustomMotif: '',
  items: [],
  paymentMode: 'Espèces',
  libreTitle: 'Note Médicale',
  libreContent: '',
  libreCustomPatient: '',
  libreCustomDate: '',
  libreHideHeader: false,
  librePageSize: 'A5',
  libreAlignment: 'justify',
  docDate: '2026-08-16',
  selectedTeethFromOdontogram: [],
  smartSuggestion: null,
  installments: [],
} as any;

describe('P3 Document Libre automatic preview guard', () => {
  it('skips preview while the content is empty', () => {
    expect(shouldSkipInvalidLibrePreview(baseParams)).toBe(true);
  });

  it('skips preview while the title is blank', () => {
    expect(
      shouldSkipInvalidLibrePreview({
        ...baseParams,
        libreTitle: '   ',
        libreContent: 'Texte du praticien.',
      }),
    ).toBe(true);
  });

  it('allows preview once title and content are valid', () => {
    expect(
      shouldSkipInvalidLibrePreview({
        ...baseParams,
        libreContent: 'Texte du praticien.',
      }),
    ).toBe(false);
  });

  it('does not apply the Libre guard to the certificate tab', () => {
    expect(
      shouldSkipInvalidLibrePreview({
        ...baseParams,
        activeTab: 'certificat',
      }),
    ).toBe(false);
  });
});
