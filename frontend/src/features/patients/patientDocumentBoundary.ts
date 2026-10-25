import { useAccountingStore } from '../admin/store/useAccountingStore';
import { isPrescriptionDirty, setPrescriptionDirty } from '../admin/DocumentStudio/PrescriptionDirtyState';
import { isCertificateDirty, setCertificateDirty } from '../admin/DocumentStudio/CertificateDirtyState';
import { isInstallmentDirty, setInstallmentDirty } from '../admin/DocumentStudio/InstallmentDirtyState';
import { isLibreDirty, setLibreDirty } from '../admin/DocumentStudio/LibreDirtyState';
import { isP7Dirty, setP7Dirty } from '../admin/DocumentStudio/P7DirtyState';
import { usePatientStore } from '../../stores/usePatientStore';

/**
 * Honoraires/Devis may be edited BEFORE an act description exists.
 * Never infer "clean" solely from nonempty act labels: a price, payment
 * choice or treatment grouping is itself a clinical financial draft.
 * Ignore catalog suggestions and visual-only toggles, which are not drafts.
 */
const hasAccountingDraft = () => {
  const state = useAccountingStore.getState();
  return state.items.some(item =>
    Boolean(item.description.trim()) ||
    Boolean(item.dent.trim()) ||
    item.price !== 0 ||
    Boolean(item.toothNumbers?.length) ||
    Boolean(item.odontogramNotes?.trim())
  ) ||
    state.groupTreatmentName.trim() !== '' ||
    state.groupTreatmentPrice !== '' ||
    state.paymentMode !== '' ||
    state.paymentStatus !== 'EN_ATTENTE' ||
    state.isAccounted !== true ||
    state.isGlobalNote ||
    state.installments.length > 0 ||
    state.groupSelectedTeeth.length > 0;
};

export const hasUnsavedPatientDocumentDraft = () =>
  isPrescriptionDirty() ||
  isCertificateDirty() ||
  hasAccountingDraft() ||
  isInstallmentDirty() ||
  isLibreDirty() ||
  isP7Dirty();

export const clearPatientDocumentDraftBoundary = () => {
  setPrescriptionDirty(false);
  setCertificateDirty(false);
  setInstallmentDirty(false);
  setLibreDirty(false);
  setP7Dirty(false);
  useAccountingStore.getState().reset();
  usePatientStore.getState().setEditingDoc(null);
};

/**
 * Clears state that must never survive a patient identity boundary.
 * Patient caches are intentionally preserved; only active document/editing state
 * is invalidated.
 */
export const resetPatientDocumentBoundary = () => {
  clearPatientDocumentDraftBoundary();
};