import { describe, expect, it } from 'vitest';

import {
  accountingDocumentFingerprint,
  isAccountingDocumentDirty,
} from './AccountingDirtyStatePolicy';

const rows = [{
  description: 'Composite',
  dent: '16',
  price: 700,
  toothNumbers: [16],
  odontogramSurfaces: ['M', 'O'],
  odontogramNotes: 'Carie profonde',
  odontogramTreatmentCode: 'COMP2',
}];

describe('P3-G accounting dirty state', () => {
  it('treats an archived/reopened fingerprint as clean', () => {
    const baseline = accountingDocumentFingerprint('devis', rows, '2026-08-16');
    expect(isAccountingDocumentDirty('devis', rows, baseline, '2026-08-16')).toBe(false);
  });

  it('detects financial, odontogram, order and document-date changes', () => {
    const baseline = accountingDocumentFingerprint('devis', rows, '2026-08-16');
    expect(isAccountingDocumentDirty('devis', [{ ...rows[0], price: 800 }], baseline, '2026-08-16')).toBe(true);
    expect(isAccountingDocumentDirty('devis', [{ ...rows[0], odontogramNotes: 'Note modifiée' }], baseline, '2026-08-16')).toBe(true);
    expect(isAccountingDocumentDirty('devis', [rows[0], { ...rows[0], description: 'Couronne' }], baseline, '2026-08-16')).toBe(true);
    expect(isAccountingDocumentDirty('devis', rows, baseline, '2026-08-17')).toBe(true);
  });

  it('treats Devis to Honoraires as a new dirty financial document', () => {
    const baseline = accountingDocumentFingerprint('devis', rows, '2026-08-16');
    expect(isAccountingDocumentDirty('honoraires', rows, baseline, '2026-08-16')).toBe(true);
  });

  it('does not warn for an empty document', () => {
    expect(isAccountingDocumentDirty('devis', [], null, '2026-08-16')).toBe(false);
    expect(isAccountingDocumentDirty('devis', [{ description: '   ', dent: '', price: 0 }], null, '2026-08-16')).toBe(false);
  });
});
