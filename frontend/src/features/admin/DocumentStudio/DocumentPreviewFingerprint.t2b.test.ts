import { describe, expect, it } from 'vitest';
import { documentPreviewFingerprint, type DocumentPreviewFingerprintInput } from './DocumentPreviewFingerprint';

const baseline: DocumentPreviewFingerprintInput = {
  patientId: '42',
  activeTab: 'libre',
  docDate: '2026-08-16',
  drugs: [],
  certifType: '',
  certifDays: 0,
  certifStartDate: '',
  certifCustomMotif: '',
  items: [],
  paymentMode: '',
  paymentStatus: 'EN_ATTENTE',
  isGlobalNote: false,
  installments: [],
  libreTitle: 'Note',
  libreContent: 'Contenu',
  libreCustomPatient: '',
  libreCustomDate: '',
  libreHideHeader: false,
  librePageSize: 'A5',
  libreAlignment: 'justify',
  showLegalAnnotations: true,
  echeancierPayload: null,
};

describe('Document preview fingerprint', () => {
  it('is stable for the same preview input', () => {
    expect(documentPreviewFingerprint(baseline)).toBe(documentPreviewFingerprint({ ...baseline }));
  });

  it.each([
    ['patientId', '43'],
    ['activeTab', 'certificat'],
    ['docDate', '2026-08-17'],
    ['certifCustomMotif', 'Motif modifié'],
    ['paymentMode', 'TPE'],
    ['paymentStatus', 'PAYE'],
    ['isGlobalNote', true],
    ['libreCustomPatient', 'Nom personnalisé'],
    ['libreCustomDate', '17/08/2026'],
    ['libreHideHeader', true],
    ['librePageSize', 'A4'],
    ['libreAlignment', 'center'],
    ['showLegalAnnotations', false],
  ] as const)('changes when %s changes', (key, value) => {
    const changed = { ...baseline, [key]: value } as DocumentPreviewFingerprintInput;
    expect(documentPreviewFingerprint(changed)).not.toBe(documentPreviewFingerprint(baseline));
  });

  it('changes when nested document collections change', () => {
    expect(documentPreviewFingerprint({ ...baseline, drugs: [{ name: 'X' }] })).not.toBe(documentPreviewFingerprint(baseline));
    expect(documentPreviewFingerprint({ ...baseline, items: [{ description: 'Acte', price: 100 }] })).not.toBe(documentPreviewFingerprint(baseline));
    expect(documentPreviewFingerprint({ ...baseline, installments: [{ amount: 100 }] })).not.toBe(documentPreviewFingerprint(baseline));
    expect(documentPreviewFingerprint({ ...baseline, echeancierPayload: { total: 100 } })).not.toBe(documentPreviewFingerprint(baseline));
  });
});
