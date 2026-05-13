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
  lastPatientId: number | null;
  lastFetchTime: number | null;
  isLoading: boolean;
  
  // Actions
  setInsights: (insights: Insight[]) => void;
  setIntelligenceScore: (score: number) => void;
  setDockPosition: (pos: { x: number; y: number }) => void;
  setAssistantExpanded: (expanded: boolean) => void;
  fetchTreatmentPlan: (patientId: number) => Promise<void>;
  
  // Async Actions
  fetchPatientIntelligence: (patientId: number) => Promise<void>;
  auditDocument: (patientId: number, contextType: string, docData: any) => Promise<void>;
}

export const useEliteStore = create<EliteState>()(
  persist(
    (set, get) => ({
      insights: [],
      intelligenceScore: 85,
      dockPosition: { x: 0, y: 0 },
      isAssistantExpanded: false,
      treatmentPlan: null,
      lastPatientId: null,
      lastFetchTime: null,
      isLoading: false,

      setInsights: (insights) => set({ insights }),
      setIntelligenceScore: (intelligenceScore) => set({ intelligenceScore }),
      setDockPosition: (dockPosition) => set({ dockPosition }),
      setAssistantExpanded: (isAssistantExpanded) => set({ isAssistantExpanded }),
      
      fetchTreatmentPlan: async (patientId: number) => {
        set({ isLoading: true });
        try {
          const response = await api.get(`/intelligence/patient/${patientId}/treatment-plan`);
          set({ 
            treatmentPlan: response.data,
            isLoading: false 
          });
        } catch (error) {
          console.error("Error fetching treatment plan:", error);
          set({ isLoading: false });
        }
      },

      fetchPatientIntelligence: async (patientId: number) => {
        const state = get();
        const now = Date.now();
        
        // Cache Logic: Si c'est le même patient et que le fetch date de moins de 5 min
        if (state.lastPatientId === patientId && state.lastFetchTime && (now - state.lastFetchTime < 300000)) {
          return;
        }

        set({ isLoading: true });
        try {
          const response = await api.get(`/intelligence/patient/${patientId}`);
          set({ 
            insights: response.data.insights || [],
            intelligenceScore: response.data.intelligence_score || 85,
            lastPatientId: patientId,
            lastFetchTime: now,
            isLoading: false
          });
        } catch (error) {
          console.error("Error fetching intelligence:", error);
          set({ isLoading: false });
        }
      },

      auditDocument: async (patientId: number, contextType: string, docData: any) => {
        set({ isLoading: true });
        try {
          const response = await api.post(`/intelligence/patient/${patientId}/audit?context_type=${contextType}`, docData);
          set({ 
            insights: response.data.insights || [],
            intelligenceScore: response.data.intelligence_score || 85,
            isLoading: false
          });
        } catch (error) {
          console.error("Error auditing document:", error);
          set({ isLoading: false });
        }
      }
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
