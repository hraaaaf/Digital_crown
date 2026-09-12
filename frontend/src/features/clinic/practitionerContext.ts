import { create } from 'zustand';

export interface ClinicPractitioner {
  id: number;
  name: string;
  appointmentCount?: number;
  isFallback?: boolean;
}

interface PractitionerContextState {
  practitioners: ClinicPractitioner[];
  selectedPractitionerId: number | null;
  selectedPractitionerName: string | null;
  setPractitioners: (practitioners: ClinicPractitioner[]) => void;
  selectPractitioner: (practitioner: ClinicPractitioner) => void;
  resetPractitioners: () => void;
}

export const usePractitionerContextStore = create<PractitionerContextState>((set) => ({
  practitioners: [],
  selectedPractitionerId: null,
  selectedPractitionerName: null,

  setPractitioners: (practitioners) => set((state) => {
    const selected = practitioners.find(
      (practitioner) => practitioner.id === state.selectedPractitionerId,
    );
    const fallback = selected ?? practitioners[0] ?? null;

    return {
      practitioners,
      selectedPractitionerId: fallback?.id ?? null,
      selectedPractitionerName: fallback?.name ?? null,
    };
  }),

  selectPractitioner: (practitioner) => set({
    selectedPractitionerId: practitioner.id,
    selectedPractitionerName: practitioner.name,
  }),

  resetPractitioners: () => set({
    practitioners: [],
    selectedPractitionerId: null,
    selectedPractitionerName: null,
  }),
}));
