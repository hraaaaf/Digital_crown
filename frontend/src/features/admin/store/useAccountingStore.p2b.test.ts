import { beforeEach, describe, expect, it } from 'vitest';
import { PARTIAL_PAYMENT_DISABLED_REASON } from '../DocumentStudio/AccountingPaymentPolicy';
import { useAccountingStore } from './useAccountingStore';

describe('useAccountingStore P2-B', () => {
  beforeEach(() => {
    useAccountingStore.getState().reset();
  });

  it('refuse PARTIEL sans changer le statut courant', () => {
    useAccountingStore.getState().setPaymentStatus('PARTIEL');

    const state = useAccountingStore.getState();
    expect(state.paymentStatus).toBe('EN_ATTENTE');
    expect(state.paymentStatusGuardMessage).toBe(PARTIAL_PAYMENT_DISABLED_REASON);
  });

  it('autorise PAYE et efface le message de garde', () => {
    useAccountingStore.getState().setPaymentStatus('PARTIEL');
    useAccountingStore.getState().setPaymentStatus('PAYE');

    const state = useAccountingStore.getState();
    expect(state.paymentStatus).toBe('PAYE');
    expect(state.paymentStatusGuardMessage).toBeNull();
  });

  it('permet de fermer explicitement le message de garde', () => {
    useAccountingStore.getState().setPaymentStatus('PARTIEL');
    useAccountingStore.getState().clearPaymentStatusGuard();

    expect(useAccountingStore.getState().paymentStatusGuardMessage).toBeNull();
  });
});
