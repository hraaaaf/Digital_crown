import { describe, expect, it } from 'vitest';
import { documentPreviewFingerprint, type DocumentPreviewFingerprintInput } from './DocumentPreviewFingerprint';

const baseInput = (): DocumentPreviewFingerprintInput => ({
  activeTab: 'libre',
  patientId: '42',
  docDate: '2026-08-16',
  drugs: [],
  certificate: { type: '', days: 0, startDate: '', customReason: '' },
  accounting: {
    items: [],
    paymentMode: '',
    paymentStatus: 'EN_ATTENTE',
    installments: [],
    isGlobalNote: false,
    selectedTeeth: [],
  },
  libre: {
    title: 'Note Médicale',
    content: 'Texte',
    customPatient: '',
    customDate: '',
    hideHeader: false,
    pageSize: 'A5',
    alignment: 'justify',
  },
  showLegalAnnotations: true,
  installmentPayload: null,
});

describe('Document preview fingerprint', () => {
  it('is deterministic even when object key insertion order differs', () => {
    const first = baseInput();
    const second = JSON.parse(JSON.stringify(first)) as DocumentPreviewFingerprintInput;
    second.accounting = {
      selectedTeeth: [],
      isGlobalNote: false,
      installments: [],
      paymentStatus: 'EN_ATTENTE',
      paymentMode: '',
      items: [],
    };

    expect(documentPreviewFingerprint(first)).toBe(documentPreviewFingerprint(second));
  });

  it.each([
    ['libre custom patient', (input: DocumentPreviewFingerprintInput) => { input.libre!.customPatient = 'Mme A'; }],
    ['libre custom date', (input: DocumentPreviewFingerprintInput) => { input.libre!.customDate = '16/08/2026'; }],
    ['libre hide header', (input: DocumentPreviewFingerprintInput) => { input.libre!.hideHeader = true; }],
    ['libre page size', (input: DocumentPreviewFingerprintInput) => { input.libre!.pageSize = 'A4'; }],
    ['libre alignment', (input: DocumentPreviewFingerprintInput) => { input.libre!.alignment = 'center'; }],
    ['payment status', (input: DocumentPreviewFingerprintInput) => { input.accounting!.paymentStatus = 'PAYE'; }],
    ['global note flag', (input: DocumentPreviewFingerprintInput) => { input.accounting!.isGlobalNote = true; }],
    ['installments', (input: DocumentPreviewFingerprintInput) => { input.accounting!.installments = [{ amount: 100 }]; }],
    ['selected teeth', (input: DocumentPreviewFingerprintInput) => { input.accounting!.selectedTeeth = [{ tooth: 11 }]; }],
    ['legal annotations', (input: DocumentPreviewFingerprintInput) => { input.showLegalAnnotations = false; }],
    ['installment payload', (input: DocumentPreviewFingerprintInput) => { input.installmentPayload = { title: 'Plan' }; }],
  ])('changes when %s changes', (_label, mutate) => {
    const first = baseInput();
    const second = baseInput();
    mutate(second);

    expect(documentPreviewFingerprint(second)).not.toBe(documentPreviewFingerprint(first));
  });
});
