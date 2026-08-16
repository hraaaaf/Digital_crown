import { useAccountingStore } from '../admin/store/useAccountingStore';
import { usePatientStore } from '../../stores/usePatientStore';

/**
 * Clears state that must never survive a patient identity boundary.
 * Patient caches are intentionally preserved; only active document/editing state
 * is invalidated.
 */
export const resetPatientDocumentBoundary = () => {
  useAccountingStore.getState().reset();
  usePatientStore.getState().setEditingDoc(null);
};
