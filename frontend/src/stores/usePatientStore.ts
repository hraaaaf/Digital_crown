import { create } from 'zustand';
import type { Patient } from '../types';

const DOCUMENT_EDIT_ARCHIVE_KEY = 'digitalcrown:document-edit-archive-id';

interface PatientState {
  editingDoc: any | null;
  patientsCache: Patient[];
  patientsCacheLoaded: boolean;
  patientsCacheUpdatedAt: number;
  setEditingDoc: (doc: any | null) => void;
  setPatientsCache: (patients: Patient[]) => void;
}

const persistEditingArchiveId = (doc: any | null) => {
  if (typeof window === 'undefined') return;
  const rawId = doc?.id;
  const canonicalId = typeof rawId === 'number'
    ? rawId
    : (typeof rawId === 'string' && /^\d+$/.test(rawId) ? Number(rawId) : null);

  if (canonicalId !== null) {
    window.sessionStorage.setItem(DOCUMENT_EDIT_ARCHIVE_KEY, String(canonicalId));
  } else {
    window.sessionStorage.removeItem(DOCUMENT_EDIT_ARCHIVE_KEY);
  }
};

export const usePatientStore = create<PatientState>((set) => ({
  editingDoc: null,
  patientsCache: [],
  patientsCacheLoaded: false,
  patientsCacheUpdatedAt: 0,
  setEditingDoc: (doc) => {
    persistEditingArchiveId(doc);
    set({ editingDoc: doc });
  },
  setPatientsCache: (patients) => set({ patientsCache: patients, patientsCacheLoaded: true, patientsCacheUpdatedAt: Date.now() }),
}));

if (typeof window !== 'undefined') {
  window.addEventListener('digitalcrown:document-edit-complete', () => {
    usePatientStore.getState().setEditingDoc(null);
  });
}
