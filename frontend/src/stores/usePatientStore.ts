import { create } from 'zustand';

interface PatientState {
  editingDoc: any | null;
  setEditingDoc: (doc: any | null) => void;
}

export const usePatientStore = create<PatientState>((set) => ({
  editingDoc: null,
  setEditingDoc: (doc) => set({ editingDoc: doc }),
}));
