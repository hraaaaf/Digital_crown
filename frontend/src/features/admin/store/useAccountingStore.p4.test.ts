import { beforeEach, describe, expect, it } from 'vitest';
import { useAccountingStore } from './useAccountingStore';

describe('P4 financial draft state', () => {
  beforeEach(() => {
    useAccountingStore.getState().reset();
  });

  it('démarre sans mode de règlement implicite', () => {
    const state = useAccountingStore.getState();
    expect(state.paymentStatus).toBe('EN_ATTENTE');
    expect(state.paymentMode).toBe('');
    expect(state.isGlobalNote).toBe(false);
    expect(state.installments).toEqual([]);
  });

  it('n’accepte pas PARTIEL dans le flux documentaire', () => {
    useAccountingStore.getState().setPaymentStatus('PARTIEL');
    const state = useAccountingStore.getState();
    expect(state.paymentStatus).toBe('EN_ATTENTE');
    expect(state.paymentStatusGuardMessage).toBeTruthy();
  });

  it('conserve uniquement un mode explicitement choisi par le praticien', () => {
    useAccountingStore.getState().setPaymentStatus('PAYE');
    expect(useAccountingStore.getState().paymentMode).toBe('');

    useAccountingStore.getState().setPaymentMode('TPE');
    expect(useAccountingStore.getState().paymentMode).toBe('TPE');
  });
});
