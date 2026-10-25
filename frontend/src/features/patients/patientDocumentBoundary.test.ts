import { beforeEach, describe, expect, it } from 'vitest';
import { useAccountingStore } from '../admin/store/useAccountingStore';
import { setPrescriptionDirty } from '../admin/DocumentStudio/PrescriptionDirtyState';
import { setCertificateDirty } from '../admin/DocumentStudio/CertificateDirtyState';
import { setInstallmentDirty } from '../admin/DocumentStudio/InstallmentDirtyState';
import { setLibreDirty } from '../admin/DocumentStudio/LibreDirtyState';
import { setP7Dirty } from '../admin/DocumentStudio/P7DirtyState';
import { usePatientStore } from '../../stores/usePatientStore';
import {
  hasUnsavedPatientDocumentDraft,
  resetPatientDocumentBoundary,
} from './patientDocumentBoundary';

describe('resetPatientDocumentBoundary', () => {
  beforeEach(() => {
    resetPatientDocumentBoundary();
  });

  it('blocks Honoraires when a financial value is changed before an act description', () => {
    const store = useAccountingStore.getState();
    expect(hasUnsavedPatientDocumentDraft()).toBe(false);

    store.setItems([{ id: 1, description: '', dent: '', price: 250 }]);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setPaymentMode('Virement');
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setGroupTreatmentName('Traitement synthétique');
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setGroupTreatmentPrice(800);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setGroupSelectedTeeth([11]);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setPaymentStatus('PAYE');
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setIsAccounted(false);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    useAccountingStore.getState().setInstallments([
      {id:1,date:'2026-10-23',amount:800,label:'Synthetic installment'},
    ]);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();

    expect(hasUnsavedPatientDocumentDraft()).toBe(false);
  });

  it('does not falsely classify catalog suggestion and view toggles as an accounting draft', () => {
    useAccountingStore.getState().setActSuggestions([{id:'test',name:'Catalogue synthétique'}]);
    useAccountingStore.getState().setShowOdontoPanoramique(false);
    expect(hasUnsavedPatientDocumentDraft()).toBe(false);
  });

  it('keeps actual prescription and certificate dirty flags independent from Honoraires', () => {
    setPrescriptionDirty(true);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();
    setCertificateDirty(true);
    expect(hasUnsavedPatientDocumentDraft()).toBe(true);
    resetPatientDocumentBoundary();
    expect(hasUnsavedPatientDocumentDraft()).toBe(false);
  });

  it('detects and clears every patient-scoped document dirty source', () => {
    setPrescriptionDirty(true);
    setCertificateDirty(true);
    setInstallmentDirty(true);
    setLibreDirty(true);
    setP7Dirty(true);

    const accounting = useAccountingStore.getState();
    accounting.setItems([{ id: 1, description: 'Acte patient A', dent: '11', price: 900 }]);
    accounting.setPaymentMode('Virement');
    accounting.setInstallments([{ id: 1, date: '2026-09-01', amount: 900, label: 'Acompte A' }]);
    accounting.setPaymentStatus('PAYE');
    accounting.setIsGlobalNote(true);
    accounting.setGroupSelectedTeeth([11, 12]);
    accounting.setActSuggestions([{ id: 'a', name: 'Suggestion A' }]);
    usePatientStore.getState().setEditingDoc({ id: 44, patient_id: 1, type: 'devis' });

    expect(hasUnsavedPatientDocumentDraft()).toBe(true);

    resetPatientDocumentBoundary();

    const resetAccounting = useAccountingStore.getState();
    expect(hasUnsavedPatientDocumentDraft()).toBe(false);
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