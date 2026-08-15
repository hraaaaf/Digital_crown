import { describe, expect, it } from 'vitest';
import {
  reconcileInstallments,
  validateInstallmentAmounts,
} from './AccountingInstallmentPolicy';

describe('AccountingInstallmentPolicy P2-E', () => {
  it('réconcilie exactement au centime', () => {
    expect(reconcileInstallments(1000, [{ amount: 333.33 }, { amount: 333.33 }, { amount: 333.34 }])).toEqual({
      billedTotal: 1000,
      installmentTotal: 1000,
      difference: 0,
      reconciled: true,
    });
  });

  it('refuse une somme d’échéances inférieure au total facturé', () => {
    expect(validateInstallmentAmounts(1000, [{ amount: 400 }, { amount: 500 }])).toMatch(/inférieure.*100\.00 MAD/);
  });

  it('refuse une somme d’échéances supérieure au total facturé', () => {
    expect(validateInstallmentAmounts(1000, [{ amount: 600 }, { amount: 500 }])).toMatch(/supérieure.*100\.00 MAD/);
  });

  it('refuse les échéances nulles ou négatives', () => {
    expect(validateInstallmentAmounts(1000, [{ amount: 0 }, { amount: 1000 }])).toMatch(/strictement positif/);
    expect(validateInstallmentAmounts(1000, [{ amount: -50 }, { amount: 1050 }])).toMatch(/strictement positif/);
  });
});
