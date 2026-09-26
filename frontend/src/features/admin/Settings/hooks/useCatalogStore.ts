import { create } from 'zustand';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';

export type CatalogDentition = 'PRIMARY' | 'PERMANENT';
export type CatalogToothType = 'INCISOR' | 'CANINE' | 'PREMOLAR' | 'MOLAR';
export type CatalogTreatmentArea = 'SURFACE' | 'TOOTH' | 'TOOTH_RANGE' | 'QUADRANT' | 'ARCH' | 'MOUTH';
export type CatalogSelectionMode = 'INDIVIDUAL' | 'GROUP' | 'GENERAL';

export interface CatalogActApplicability {
  dentitions: CatalogDentition[];
  tooth_types: CatalogToothType[];
  treatment_areas: CatalogTreatmentArea[];
  selection_modes: CatalogSelectionMode[];
  requires_present_tooth: boolean;
  requires_missing_tooth: boolean;
  min_selected_teeth: number;
  max_selected_teeth?: number | null;
  age_min?: number | null;
  age_max?: number | null;
  suggestion_priority: number;
  searchable_when_not_suggested: boolean;
}

export const DEFAULT_CATALOG_ACT_APPLICABILITY: CatalogActApplicability = {
  dentitions: [],
  tooth_types: [],
  treatment_areas: [],
  selection_modes: [],
  requires_present_tooth: false,
  requires_missing_tooth: false,
  min_selected_teeth: 0,
  max_selected_teeth: null,
  age_min: null,
  age_max: null,
  suggestion_priority: 0,
  searchable_when_not_suggested: true,
};

export const normalizeCatalogActApplicability = (
  value?: Partial<CatalogActApplicability>,
): CatalogActApplicability => ({
  ...DEFAULT_CATALOG_ACT_APPLICABILITY,
  ...(value || {}),
  dentitions: [...(value?.dentitions || [])],
  tooth_types: [...(value?.tooth_types || [])],
  treatment_areas: [...(value?.treatment_areas || [])],
  selection_modes: [...(value?.selection_modes || [])],
});

export interface CatalogAct {
  id: number;
  specialty_id: number;
  name: string;
  code?: string;
  base_price: number;
  color?: string;
  is_active: boolean;
  applicability?: Partial<CatalogActApplicability>;
}

export interface Pathology {
  id: number;
  specialty_id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Specialty {
  id: number;
  name: string;
  color?: string;
  pathologies: Pathology[];
  acts: CatalogAct[];
}

type SpecialtyMutation = { name: string; color?: string };
type PathologyMutation = { name: string; description?: string; is_active?: boolean };
type ActMutation = { name: string; base_price: number; code?: string; color?: string; is_active?: boolean; applicability?: Partial<CatalogActApplicability> };

type PathologyUpdate = Partial<PathologyMutation>;
type ActUpdate = Partial<ActMutation>;

interface CatalogState {
  specialties: Specialty[];
  loading: boolean;
  readError: string | null;
  fetchCatalog: () => Promise<void>;
  createSpecialty: (data: SpecialtyMutation) => Promise<boolean>;
  updateSpecialty: (id: number, data: Partial<SpecialtyMutation>) => Promise<boolean>;
  createPathology: (specialtyId: number, data: PathologyMutation) => Promise<boolean>;
  updatePathology: (pathologyId: number, data: PathologyUpdate) => Promise<boolean>;
  createAct: (specialtyId: number, data: ActMutation) => Promise<boolean>;
  updateAct: (actId: number, data: ActUpdate) => Promise<boolean>;
}

const mutationError = (error: unknown, fallback: string) => {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  toast.error(typeof detail === 'string' && detail.trim() ? detail : fallback);
};

export const useCatalogStore = create<CatalogState>((set, get) => ({
  specialties: [],
  loading: false,
  readError: null,

  fetchCatalog: async () => {
    set({ loading: true, readError: null });
    try {
      const res = await api.get('/catalog/specialties');
      set({ specialties: res.data, readError: null });
    } catch (err) {
      console.error(err);
      set({ readError: "Impossible de charger le catalogue réel du cabinet. Aucune modification n'est autorisée tant que la lecture n'a pas réussi." });
      toast.error('Erreur lors du chargement du catalogue');
    } finally {
      set({ loading: false });
    }
  },

  createSpecialty: async (data) => {
    if (get().readError) return false;
    try {
      await api.post('/catalog/specialties', data);
      toast.success('Spécialité ajoutée');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, "Impossible d'ajouter la spécialité");
      return false;
    }
  },

  updateSpecialty: async (id, data) => {
    if (get().readError) return false;
    try {
      await api.put(`/catalog/specialties/${id}`, data);
      toast.success('Spécialité modifiée');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, 'Impossible de modifier la spécialité');
      return false;
    }
  },

  createPathology: async (specialtyId, data) => {
    if (get().readError) return false;
    try {
      await api.post(`/catalog/specialties/${specialtyId}/pathologies`, data);
      toast.success('Pathologie ajoutée');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, "Impossible d'ajouter la pathologie");
      return false;
    }
  },

  updatePathology: async (pathologyId, data) => {
    if (get().readError) return false;
    try {
      await api.put(`/catalog/pathologies/${pathologyId}`, data);
      toast.success('Pathologie modifiée');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, 'Impossible de modifier la pathologie');
      return false;
    }
  },

  createAct: async (specialtyId, data) => {
    if (get().readError) return false;
    try {
      await api.post(`/catalog/specialties/${specialtyId}/acts`, data);
      toast.success('Acte ajouté');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, "Impossible d'ajouter l'acte");
      return false;
    }
  },

  updateAct: async (actId, data) => {
    if (get().readError) return false;
    try {
      await api.put(`/catalog/acts/${actId}`, data);
      toast.success('Acte modifié');
      await get().fetchCatalog();
      return true;
    } catch (error) {
      mutationError(error, "Impossible de modifier l'acte");
      return false;
    }
  },
}));
