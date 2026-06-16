import { create } from 'zustand';
import type { Patient } from '../types';

interface PatientState {
  editingDoc: any | null;
  patientsCache: Patient[];
  patientsCacheLoaded: boolean;
  patientsCacheUpdatedAt: number;
  setEditingDoc: (doc: any | null) => void;
  setPatientsCache: (patients: Patient[]) => void;
}

export const usePatientStore = create<PatientState>((set) => ({
  editingDoc: null,
  patientsCache: [],
  patientsCacheLoaded: false,
  patientsCacheUpdatedAt: 0,
  setEditingDoc: (doc) => set({ editingDoc: doc }),
  setPatientsCache: (patients) => set({ patientsCache: patients, patientsCacheLoaded: true, patientsCacheUpdatedAt: Date.now() }),
}));
