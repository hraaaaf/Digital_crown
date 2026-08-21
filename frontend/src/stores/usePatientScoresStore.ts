import { create } from 'zustand';
import { api } from '../services/api';

export interface PatientScoreData {
  score: number | null;
  grade: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE' | null;
  is_manual: boolean;
  comment?: string | null;
  details: {
    assiduite_score?: null;
    solvabilite_score?: null;
    rdv_honores: number;
    rdv_annules: number;
    rdv_total_observe: number;
    total_facture: number;
    total_encaisse: number;
    remaining_due: number | null;
    has_billing_data: boolean;
  };
}

interface PatientScoresState {
  scores: Record<number, PatientScoreData>;
  loading: boolean;
  loaded: boolean;
  fetchScores: (force?: boolean) => Promise<void>;
}

let inflight: Promise<void> | null = null;

export const usePatientScoresStore = create<PatientScoresState>((set, get) => ({
  scores: {},
  loading: false,
  loaded: false,

  fetchScores: async (force = false) => {
    if (!force && (get().loaded || get().loading)) return;
    if (inflight) return inflight;

    set({ loading: true });
    inflight = (async () => {
      try {
        const res = await api.get('/patients/scores');
        const map: Record<number, PatientScoreData> = {};
        for (const [key, value] of Object.entries(res.data || {})) {
          map[Number(key)] = value as PatientScoreData;
        }
        set({ scores: map, loaded: true });
      } catch (err) {
        console.error('Erreur chargement repères patients', err);
      } finally {
        set({ loading: false });
        inflight = null;
      }
    })();
    return inflight;
  },
}));
