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
    const baseline = accountingDocumentFingerprint('devis', rows);
    expect(isAccountingDocumentDirty('devis', rows, baseline)).toBe(false);
  });

  it('detects financial, odontogram and order changes', () => {
    const baseline = accountingDocumentFingerprint('devis', rows);
    expect(isAccountingDocumentDirty('devis', [{ ...rows[0], price: 800 }], baseline)).toBe(true);
    expect(isAccountingDocumentDirty('devis', [{ ...rows[0], odontogramNotes: 'Note modifiée' }], baseline)).toBe(true);
    expect(isAccountingDocumentDirty('devis', [rows[0], { ...rows[0], description: 'Couronne' }], baseline)).toBe(true);
  });

  it('treats Devis to Honoraires as a new dirty financial document', () => {
    const baseline = accountingDocumentFingerprint('devis', rows);
    expect(isAccountingDocumentDirty('honoraires', rows, baseline)).toBe(true);
  });

  it('does not warn for an empty document', () => {
    expect(isAccountingDocumentDirty('devis', [], null)).toBe(false);
    expect(isAccountingDocumentDirty('devis', [{ description: '   ', dent: '', price: 0 }], null)).toBe(false);
  });
});
