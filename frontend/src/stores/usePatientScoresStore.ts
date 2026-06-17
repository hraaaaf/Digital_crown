import { create } from 'zustand';
import { api } from '../services/api';

export interface PatientScoreData {
  score: number;
  grade: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  is_manual: boolean;
  comment?: string;
  details: {
    assiduite_score: number;
    solvabilite_score: number;
    rdv_honores?: number;
    rdv_annules?: number;
    total_facture?: number;
    total_encaisse?: number;
  };
}

interface PatientScoresState {
  scores: Record<number, PatientScoreData>;
  loading: boolean;
  loaded: boolean;
  /** Charge les scores de TOUS les patients en un seul appel batch. */
  fetchScores: (force?: boolean) => Promise<void>;
}

let _inflight: Promise<void> | null = null;

export const usePatientScoresStore = create<PatientScoresState>((set, get) => ({
  scores: {},
  loading: false,
  loaded: false,

  fetchScores: async (force = false) => {
    if (!force && (get().loaded || get().loading)) return;
    if (_inflight) return _inflight; // dédoublonne les appels concurrents (N badges montés en même temps)

    set({ loading: true });
    _inflight = (async () => {
      try {
        const res = await api.get('/patients/scores');
        // Les clés JSON sont des strings → on normalise en number
        const map: Record<number, PatientScoreData> = {};
        for (const [k, v] of Object.entries(res.data || {})) {
          map[Number(k)] = v as PatientScoreData;
        }
        set({ scores: map, loaded: true });
      } catch (err) {
        console.error('Erreur chargement scores patients', err);
      } finally {
        set({ loading: false });
        _inflight = null;
      }
    })();
    return _inflight;
  },
}));
