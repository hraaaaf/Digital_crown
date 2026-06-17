import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AnomalyCategory = 'Conservatrice' | 'Endodontie' | 'Parodontie' | 'Chirurgie' | 'Prothèse' | 'ATM/Sinus';

export interface AnomalyDefinition {
  id: string;
  label: string;
  category: AnomalyCategory;
  isMultiTooth?: boolean;
}

/** Constats généraux (sur toute la bouche, non rattachés à une dent). */
export interface GlobalFindingDefinition {
  id: string;
  label: string;
  group: 'Parodonte' | 'Édentement' | 'Denture';
}

export const GLOBAL_FINDINGS: GlobalFindingDefinition[] = [
  { id: 'alveolyse_gen_legere', label: 'Alvéolyse généralisée légère', group: 'Parodonte' },
  { id: 'alveolyse_gen_moderee', label: 'Alvéolyse généralisée modérée', group: 'Parodonte' },
  { id: 'alveolyse_gen_severe', label: 'Alvéolyse généralisée sévère', group: 'Parodonte' },
  { id: 'parodontite_gen', label: 'Maladie parodontale généralisée', group: 'Parodonte' },
  { id: 'edentement_total_max', label: 'Édentement total maxillaire', group: 'Édentement' },
  { id: 'edentement_total_mand', label: 'Édentement total mandibulaire', group: 'Édentement' },
  { id: 'denture_mixte', label: 'Denture mixte', group: 'Denture' },
];

export const ANOMALY_TAXONOMY: AnomalyDefinition[] = [
  // CONSERVATRICE
  { id: 'carie_email', label: 'Carie de l\'émail', category: 'Conservatrice' },
  { id: 'carie_dentinaire', label: 'Carie dentinaire', category: 'Conservatrice' },
  { id: 'carie_profonde', label: 'Carie profonde (Pulpaire)', category: 'Conservatrice' },
  { id: 'reprise_carie', label: 'Reprise sous obturation', category: 'Conservatrice' },
  { id: 'obturation_comp', label: 'Obturation composite/amalgame', category: 'Conservatrice' },
  { id: 'obturation_debord', label: 'Obturation débordante', category: 'Conservatrice' },

  // ENDODONTIE
  { id: 'lesion_periapicale', label: 'Lésion périapicale (Kyste)', category: 'Endodontie' },
  { id: 'elargissement_desmo', label: 'Élargissement desmodontal', category: 'Endodontie' },
  { id: 'tr_adequat', label: 'Traitement canalaire adéquat', category: 'Endodontie' },
  { id: 'tr_incomplet', label: 'Traitement canalaire incomplet', category: 'Endodontie' },
  { id: 'depassement_pate', label: 'Dépassement de pâte', category: 'Endodontie' },
  { id: 'instrument_fracture', label: 'Instrument fracturé', category: 'Endodontie' },
  { id: 'perforation', label: 'Faux-canal (Perforation)', category: 'Endodontie' },

  // PARODONTIE
  { id: 'alveolyse_h', label: 'Alvéolyse horizontale', category: 'Parodontie', isMultiTooth: true },
  { id: 'alveolyse_v', label: 'Alvéolyse verticale', category: 'Parodontie' },
  { id: 'furcation', label: 'Atteinte de la furcation', category: 'Parodontie' },
  { id: 'tartre', label: 'Tartre sous-gingival', category: 'Parodontie', isMultiTooth: true },

  // CHIRURGIE
  { id: 'dent_absente', label: 'Dent absente / extraite', category: 'Chirurgie' },
  { id: 'agenesie', label: 'Agénésie (germe absent)', category: 'Chirurgie' },
  { id: 'surnumeraire', label: 'Dent surnuméraire', category: 'Chirurgie' },
  { id: 'incluse', label: 'Dent incluse', category: 'Chirurgie' },
  { id: 'enclavee', label: 'Dent enclavée', category: 'Chirurgie' },
  { id: 'reste_radiculaire', label: 'Reste radiculaire', category: 'Chirurgie' },
  { id: 'resorption', label: 'Résorption radiculaire', category: 'Chirurgie' },

  // PROTHÈSE
  { id: 'couronne', label: 'Couronne unitaire', category: 'Prothèse' },
  { id: 'bridge', label: 'Bridge prothétique', category: 'Prothèse', isMultiTooth: true },
  { id: 'implant', label: 'Implant dentaire', category: 'Prothèse' },
  { id: 'appareil', label: 'Appareil / prothèse amovible', category: 'Prothèse', isMultiTooth: true },
  { id: 'peri_implantite', label: 'Péri-implantite', category: 'Prothèse' },
  { id: 'infiltration_prothese', label: 'Infiltration sous prothèse', category: 'Prothèse' },

  // ATM / SINUS / AUTRES
  { id: 'opacite_sinus', label: 'Opacité sinusienne', category: 'ATM/Sinus', isMultiTooth: true },
  { id: 'racine_sinus', label: 'Racine dans le sinus', category: 'ATM/Sinus' },
  { id: 'condyle_asymetrie', label: 'Asymétrie condylienne', category: 'ATM/Sinus' },
  { id: 'arthrose_atm', label: 'Arthrose ATM', category: 'ATM/Sinus' },
  { id: 'calcification', label: 'Calcification (Carotide/Sial.)', category: 'ATM/Sinus' },
];

interface PanoramicState {
  toothAnomalies: Record<number, string[]>;
  globalFindings: string[];
  multiSelectMode: { active: boolean; anomalyId: string | null; startFdi: number | null };

  toggleAnomaly: (fdi: number, anomalyId: string) => void;
  toggleGlobalFinding: (id: string) => void;
  startMultiSelect: (fdi: number, anomalyId: string) => void;
  finishMultiSelect: (endFdi: number) => void;
  cancelMultiSelect: () => void;
  clearAnomalies: (fdi: number) => void;
  resetAll: () => void;
}

export const usePanoramicStore = create<PanoramicState>()(persist((set) => ({

  toothAnomalies: {},
  globalFindings: [],
  multiSelectMode: { active: false, anomalyId: null, startFdi: null },

  toggleGlobalFinding: (id) => set((state) => {
    const exists = state.globalFindings.includes(id);
    return {
      globalFindings: exists
        ? state.globalFindings.filter(g => g !== id)
        : [...state.globalFindings, id],
    };
  }),

  toggleAnomaly: (fdi, anomalyId) => set((state) => {
    const anomalies = state.toothAnomalies[fdi] || [];
    const exists = anomalies.includes(anomalyId);
    
    let newAnomalies;
    if (exists) {
      newAnomalies = anomalies.filter(a => a !== anomalyId);
    } else {
      newAnomalies = [...anomalies, anomalyId];
    }

    if (newAnomalies.length === 0) {
      const nextState = { ...state.toothAnomalies };
      delete nextState[fdi];
      return { toothAnomalies: nextState };
    }

    return {
      toothAnomalies: { ...state.toothAnomalies, [fdi]: newAnomalies }
    };
  }),

  startMultiSelect: (fdi, anomalyId) => set({
    multiSelectMode: { active: true, anomalyId, startFdi: fdi }
  }),

  finishMultiSelect: (endFdi) => set((state) => {
    const { startFdi, anomalyId } = state.multiSelectMode;
    if (startFdi === null || anomalyId === null) return state;

    const nextAnomalies = { ...state.toothAnomalies };
    

    const allFdi = [
      18,17,16,15,14,13,12,11, 21,22,23,24,25,26,27,28,
      38,37,36,35,34,33,32,31, 41,42,43,44,45,46,47,48
    ];

    const startIndex = allFdi.indexOf(startFdi);
    const endIndex = allFdi.indexOf(endFdi);
    
    if (startIndex !== -1 && endIndex !== -1) {
      const min = Math.min(startIndex, endIndex);
      const max = Math.max(startIndex, endIndex);
      const range = allFdi.slice(min, max + 1);

      range.forEach(fdi => {
        const current = nextAnomalies[fdi] || [];
        if (!current.includes(anomalyId)) {
          nextAnomalies[fdi] = [...current, anomalyId];
        }
      });
    }

    return {
      toothAnomalies: nextAnomalies,
      multiSelectMode: { active: false, anomalyId: null, startFdi: null }
    };
  }),


  cancelMultiSelect: () => set({
    multiSelectMode: { active: false, anomalyId: null, startFdi: null }
  }),

  clearAnomalies: (fdi) => set((state) => {
    const nextState = { ...state.toothAnomalies };
    delete nextState[fdi];
    return { toothAnomalies: nextState };
  }),

  resetAll: () => set({ toothAnomalies: {}, globalFindings: [], multiSelectMode: { active: false, anomalyId: null, startFdi: null } }),
}), {
  name: 'panoramic-annotations',
  // On ne persiste que les données cliniques (pas l'état transitoire du multi-select).
  partialize: (state) => ({ toothAnomalies: state.toothAnomalies, globalFindings: state.globalFindings }),
}));
