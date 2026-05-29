import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Insight } from '../features/admin/DocumentStudio/EliteAssistant';
import { api } from '../services/api';

interface EliteState {
  insights: Insight[];
  intelligenceScore: number;
  dockPosition: { x: number; y: number };
  isAssistantExpanded: boolean;
  treatmentPlan: any | null;
  suggestedAppointment: any | null;
  lastPatientId: number | null;
  lastFetchTime: number | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setInsights: (insights: Insight[]) => void;
  setIntelligenceScore: (score: number) => void;
  setDockPosition: (pos: { x: number; y: number }) => void;
  setAssistantExpanded: (expanded: boolean) => void;
  clearError: () => void;
  fetchTreatmentPlan: (patientId: number) => Promise<void>;
  fetchSuggestedAppointment: (patientId: number) => Promise<void>;

  // Async Actions
  fetchPatientIntelligence: (patientId: number) => Promise<void>;
  auditDocument: (patientId: number, contextType: string, docData: any) => Promise<void>;
  computeIntelligenceScore: () => void;
}

export const useEliteStore = create<EliteState>()(
  persist(
    (set, get) => ({
      insights: [],
      intelligenceScore: 0,
      dockPosition: { x: 0, y: 0 },
      isAssistantExpanded: false,
      treatmentPlan: null,
      suggestedAppointment: null,
      lastPatientId: null,
      lastFetchTime: null,
      isLoading: false,
      error: null,

      computeIntelligenceScore: () => {
        try {
          const history = JSON.parse(localStorage.getItem('ghost_act_brain') || '{}');
          const actsCount = Object.keys(history).length;
          
          let score = 30; // Base score (système initialisé)
          
          // Bonus Apprentissage (PriceBrain)
          score += Math.min(actsCount * 5, 40); // Jusqu'à +40% (8 actes maîtrisés)
          
          // Bonus Détection (Insights actifs)
          score += Math.min(get().insights.length * 5, 30); // Jusqu'à +30% (6 alertes)

          set({ intelligenceScore: Math.min(score, 100) });
        } catch {
          set({ intelligenceScore: 30 });
        }
      },

      setInsights: (insights) => {
        set({ insights });
        get().computeIntelligenceScore();
      },
      setIntelligenceScore: (intelligenceScore) => set({ intelligenceScore }),
      setDockPosition: (dockPosition) => set({ dockPosition }),
      setAssistantExpanded: (isAssistantExpanded) => set({ isAssistantExpanded }),
      clearError: () => set({ error: null }),

      fetchTreatmentPlan: async (patientId: number) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.get(`/intelligence/patient/${patientId}/treatment-plan`);
          set({ treatmentPlan: response.data, isLoading: false });
        } catch (error: any) {
          set({ isLoading: false, error: error?.response?.data?.detail ?? 'Erreur plan de traitement' });
        }
      },

      fetchSuggestedAppointment: async (patientId: number) => {
        set({ isLoading: true, error: null });
        try {
          const res = await api.get(`/appointments/suggest/${patientId}`);
          set({ suggestedAppointment: res.data, isLoading: false });
        } catch (error: any) {
          set({ isLoading: false, error: error?.response?.data?.detail ?? 'Erreur suggestion RDV' });
        }
      },

      fetchPatientIntelligence: async (patientId: number) => {
        const state = get();
        const now = Date.now();

        if (state.lastPatientId === patientId && state.lastFetchTime && (now - state.lastFetchTime < 300000)) {
          return;
        }

        set({ isLoading: true, error: null });
        try {
          const response = await api.get(`/intelligence/patient/${patientId}`);
          set({
            insights: response.data.insights || [],
            lastPatientId: patientId,
            lastFetchTime: now,
            isLoading: false
          });
          get().computeIntelligenceScore();
        } catch (error: any) {
          set({ isLoading: false, error: error?.response?.data?.detail ?? 'Erreur intelligence patient' });
        }
      },

      auditDocument: async (patientId: number, contextType: string, docData: any) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post(`/intelligence/patient/${patientId}/audit?context_type=${contextType}`, docData);
          set({
            insights: response.data.insights || [],
            intelligenceScore: response.data.intelligence_score || 85,
            isLoading: false
          });
        } catch (error: any) {
          set({ isLoading: false, error: error?.response?.data?.detail ?? 'Erreur audit document' });
        }
      },


    }),
    {
      name: 'elite-intelligence-storage',
      partialize: (state) => ({ 
        dockPosition: state.dockPosition,
        isAssistantExpanded: state.isAssistantExpanded 
      }),
    }
  )
);
