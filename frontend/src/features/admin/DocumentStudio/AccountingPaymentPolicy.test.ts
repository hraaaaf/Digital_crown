import { describe, expect, it } from 'vitest';
import {
  getDocumentPaymentStatusOptions,
  mapPaymentModeToBackend,
  PARTIAL_PAYMENT_DISABLED_REASON,
  validateExplicitCollectedAmount,
} from './AccountingPaymentPolicy';

describe('AccountingPaymentPolicy P2-B', () => {
  it('désactive PARTIEL dans le flux document tant qu’aucun montant explicite n’est câblé', () => {
    const partial = getDocumentPaymentStatusOptions().find(option => option.id === 'PARTIEL');
    expect(partial).toEqual({
      id: 'PARTIEL',
      label: 'Partiel',
      enabled: false,
      reason: PARTIAL_PAYMENT_DISABLED_REASON,
    });
  });

  it('conserve EN_ATTENTE et PAYE disponibles', () => {
    const options = getDocumentPaymentStatusOptions();
    expect(options.find(option => option.id === 'EN_ATTENTE')?.enabled).toBe(true);
    expect(options.find(option => option.id === 'PAYE')?.enabled).toBe(true);
  });

  it('mappe les modes UI vers les valeurs backend explicites', () => {
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
