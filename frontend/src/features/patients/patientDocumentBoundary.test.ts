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