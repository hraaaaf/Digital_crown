import { useAccountingStore } from '../admin/store/useAccountingStore';
import { isPrescriptionDirty, setPrescriptionDirty } from '../admin/DocumentStudio/PrescriptionDirtyState';
import { isCertificateDirty, setCertificateDirty } from '../admin/DocumentStudio/CertificateDirtyState';
import { isInstallmentDirty, setInstallmentDirty } from '../admin/DocumentStudio/InstallmentDirtyState';
import { isLibreDirty, setLibreDirty } from '../admin/DocumentStudio/LibreDirtyState';
import { isP7Dirty, setP7Dirty } from '../admin/DocumentStudio/P7DirtyState';
import { usePatientStore } from '../../stores/usePatientStore';

const hasAccountingDraft = () =>
  useAccountingStore.getState().items.some(item => item.description.trim());

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