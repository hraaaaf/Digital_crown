import { beforeEach, describe, expect, it } from 'vitest';
import { useAccountingStore } from '../admin/store/useAccountingStore';
import { usePatientStore } from '../../stores/usePatientStore';
import { resetPatientDocumentBoundary } from './patientDocumentBoundary';

describe('resetPatientDocumentBoundary', () => {
  beforeEach(() => {
    useAccountingStore.getState().reset();
    usePatientStore.getState().setEditingDoc(null);
  });

  it('clears patient-scoped accounting and archive-edit state', () => {
    const accounting = useAccountingStore.getState();
    accounting.setItems([{ id: 1, description: 'Acte patient A', dent: '11', price: 900 }]);
    accounting.setPaymentMode('Virement');
    accounting.setInstallments([{ id: 1, date: '2026-09-01', amount: 900, label: 'Acompte A' }]);
    accounting.setPaymentStatus('PAYE');
    accounting.setIsGlobalNote(true);
    accounting.setGroupSelectedTeeth([11, 12]);
    accounting.setActSuggestions([{ id: 'a', name: 'Suggestion A' }]);
    usePatientStore.getState().setEditingDoc({ id: 44, patient_id: 1, type: 'devis' });

    resetPatientDocumentBoundary();

    const resetAccounting = useAccountingStore.getState();
    expect(resetAccounting.items).toEqual([]);
    expect(resetAccounting.paymentMode).toBe('');
    expect(resetAccounting.installments).toEqual([]);
    expect(resetAccounting.paymentStatus).toBe('EN_ATTENTE');
    expect(resetAccounting.isGlobalNote).toBe(false);
    expect(resetAccounting.groupSelectedTeeth).toEqual([]);
    expect(resetAccounting.actSuggestions).toEqual([]);
    expect(usePatientStore.getState().editingDoc).toBeNull();
  });
});
