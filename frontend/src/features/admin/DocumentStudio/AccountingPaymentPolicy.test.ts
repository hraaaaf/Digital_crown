import { describe, expect, it } from 'vitest';
import {
  mapPaymentModeToBackend,
  PARTIAL_PAYMENT_DISABLED_REASON,
  validateExplicitCollectedAmount,
} from './AccountingPaymentPolicy';

describe('AccountingPaymentPolicy P2-B', () => {
  it('documente la raison fail-closed du paiement partiel', () => {
    expect(PARTIAL_PAYMENT_DISABLED_REASON).toMatch(/montant encaissé explicite/);
  });

  it('mappe les modes UI vers les codes backend explicites', () => {
    expect(mapPaymentModeToBackend('Espèces')).toBe('ESPECES');
    expect(mapPaymentModeToBackend('Chèque')).toBe('CHEQUE');
    expect(mapPaymentModeToBackend('TPE')).toBe('CARTE');
    expect(mapPaymentModeToBackend('Virement')).toBe('VIREMENT');
  });

  it('refuse les montants encaissés nuls, négatifs ou non finis', () => {
    expect(validateExplicitCollectedAmount(0)).toBeTruthy();
    expect(validateExplicitCollectedAmount(-1)).toBeTruthy();
    expect(validateExplicitCollectedAmount(Number.NaN)).toBeTruthy();
    expect(validateExplicitCollectedAmount(250)).toBeNull();
  });
});
