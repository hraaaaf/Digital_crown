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
  
  // Actions
  setInsights: (insights: Insight[]) => void;
  setIntelligenceScore: (score: number) => void;
  setDockPosition: (pos: { x: number; y: number }) => void;
  setAssistantExpanded: (expanded: boolean) => void;
  fetchTreatmentPlan: (patientId: number) => Promise<void>;
  fetchSuggestedAppointment: (patientId: number) => Promise<void>;
  
  // Async Actions
  fetchPatientIntelligence: (patientId: number) => Promise<void>;
  auditDocument: (patientId: number, contextType: string, docData: any) => Promise<void>;
  analyzeAgendaDensity: () => Promise<void>;
}

export const useEliteStore = create<EliteState>()(
  persist(
    (set, get) => ({
      insights: [],
      intelligenceScore: 85,
      dockPosition: { x: 0, y: 0 },
      isAssistantExpanded: false,
      treatmentPlan: null,
      suggestedAppointment: null,
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

      fetchSuggestedAppointment: async (patientId: number) => {
        set({ isLoading: true });
        try {
          const res = await api.get(`/appointments/suggest/${patientId}`);
          set({ suggestedAppointment: res.data, isLoading: false });
        } catch (e) {
          console.error('Error fetching suggested appointment:', e);
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
      },

      analyzeAgendaDensity: async () => {
        try {
          const res = await api.get('/appointments/');
          const appointments = res.data || [];
          
          const now = new Date();
          const nextWeek = new Date();
          nextWeek.setDate(now.getDate() + 7);

          let extractions = 0;
          let implants = 0;
          let composites = 0;
          let endo = 0;
          let prothese = 0;

          appointments.forEach((apt: any) => {
            const aptDate = new Date(apt.datetime_start);
            if (aptDate >= now && aptDate <= nextWeek && apt.motif) {
              const motif = apt.motif.toLowerCase();
              if (motif.includes('extraction') || motif.includes('avulsion') || motif.includes('dds')) extractions++;
              if (motif.includes('implant') || motif.includes('implanto')) implants++;
              if (motif.includes('composite') || motif.includes('restauration') || motif.includes('carie') || motif.includes('plombage')) composites++;
              if (motif.includes('endo') || motif.includes('canalaire') || motif.includes('pulpectomie') || motif.includes('dévitalisation')) endo++;
              if (motif.includes('couronne') || motif.includes('bridge') || motif.includes('empreinte') || motif.includes('prothèse') || motif.includes('inlay')) prothese++;
            }
          });

          const newInsights: Insight[] = [];

          if (extractions > 0 || implants > 0) {
            newInsights.push({
              id: 'global-agenda-insight-chirurgie',
              type: 'habit',
              title: 'Intelligence Prédictive : Chirurgie',
              content: `Densité chirurgicale (7 jours) : ${extractions} extraction(s) et ${implants} implant(s) prévus. Pensez à vérifier vos stocks de compresses, sutures, lames de bistouri et cartouches d'anesthésie.`,
              source_type: 'DETERMINISTIC'
            });
          }

          if (composites > 3) {
            newInsights.push({
              id: 'global-agenda-insight-composite',
              type: 'habit',
              title: 'Intelligence Prédictive : Soins Conservateurs',
              content: `Haute activité restauratrice (${composites} composites prévus). Vérifiez vos stocks d'adhésif, de composites (teintes A2/A3 généralement), de matrices et de coins de bois.`,
              source_type: 'DETERMINISTIC'
            });
          }

          if (endo > 2) {
            newInsights.push({
              id: 'global-agenda-insight-endo',
              type: 'habit',
              title: 'Intelligence Prédictive : Endodontie',
              content: `Plusieurs traitements canalaires prévus (${endo}). Assurez-vous d'avoir suffisamment de limes rotatives, cônes de papier/gutta, digues et d'hypochlorite de sodium.`,
              source_type: 'DETERMINISTIC'
            });
          }

          if (prothese > 2) {
            newInsights.push({
              id: 'global-agenda-insight-prothese',
              type: 'habit',
              title: 'Intelligence Prédictive : Prothèse',
              content: `Densité prothétique détectée (${prothese} RDV). Vérifiez vos matériaux d'empreinte (silicone/alginate), embouts mélangeurs, fils de rétraction et ciments de scellement.`,
              source_type: 'DETERMINISTIC'
            });
          }

          // Nettoyer les anciens insights globaux
          const existingFiltered = get().insights.filter(i => !i.id.startsWith('global-agenda-insight'));
          
          if (newInsights.length > 0) {
            set({ insights: [...newInsights, ...existingFiltered] });
          } else if (existingFiltered.length !== get().insights.length) {
             set({ insights: existingFiltered });
          }

        } catch (err) {
          console.error("Failed to analyze agenda density:", err);
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
