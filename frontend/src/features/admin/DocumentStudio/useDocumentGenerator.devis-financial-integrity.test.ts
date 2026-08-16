import { describe, expect, it } from 'vitest';

import { buildAccountingFinancialFields } from './useDocumentGenerator';

describe('P3-A Devis financial isolation', () => {
  it('strips inherited installments and global-note state from Devis', () => {
    const inheritedInstallments = [
      { id: 1, date: '2026-08-20', amount: 1200, label: 'Acompte' },
      { id: 2, date: '2026-09-20', amount: 800, label: 'Solde' },
    ];

    const result = buildAccountingFinancialFields('devis', inheritedInstallments, true);

    expect(result).toEqual({ installments: [], is_global_note: false });
    expect(inheritedInstallments).toHaveLength(2);
  });

  it('preserves installments and global-note state for Honoraires', () => {
    const installments = [
      { id: 7, date: '2026-08-20', amount: 500, label: 'Versement' },
    ];

    const result = buildAccountingFinancialFields('honoraires', installments, true);

    expect(result).toEqual({ installments, is_global_note: true });
    expect(result.installments).toBe(installments);
  });
});
