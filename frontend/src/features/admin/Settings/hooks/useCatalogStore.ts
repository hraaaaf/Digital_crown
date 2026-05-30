import { create } from 'zustand';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';

export interface CatalogAct {
  id: number;
  specialty_id: number;
  name: string;
  code?: string;
  base_price: number;
  color?: string;
  is_active: boolean;
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

interface CatalogState {
  specialties: Specialty[];
  loading: boolean;
  fetchCatalog: () => Promise<void>;
  createSpecialty: (data: { name: string; color?: string }) => Promise<void>;
  updateSpecialty: (id: number, data: { name?: string; color?: string }) => Promise<void>;
  createPathology: (specialtyId: number, data: { name: string; description?: string }) => Promise<void>;
  createAct: (specialtyId: number, data: { name: string; base_price: number; code?: string; color?: string }) => Promise<void>;
}

export const useCatalogStore = create<CatalogState>((set, get) => ({
  specialties: [],
  loading: false,

  fetchCatalog: async () => {
    set({ loading: true });
    try {
      const res = await api.get('/catalog/specialties');
      set({ specialties: res.data });
    } catch (err) {
      console.error(err);
      toast.error('Erreur lors du chargement du catalogue');
    } finally {
      set({ loading: false });
    }
  },

  createSpecialty: async (data) => {
    try {
      await api.post('/catalog/specialties', data);
      toast.success('Spécialité ajoutée');
      get().fetchCatalog();
    } catch (err) {
      toast.error('Erreur ajout spécialité');
    }
  },

  updateSpecialty: async (id, data) => {
    try {
      await api.put(`/catalog/specialties/${id}`, data);
      toast.success('Spécialité modifiée');
      get().fetchCatalog();
    } catch (err) {
      toast.error('Erreur modification spécialité');
    }
  },

  createPathology: async (specialtyId, data) => {
    try {
      await api.post(`/catalog/specialties/${specialtyId}/pathologies`, data);
      toast.success('Pathologie ajoutée');
      get().fetchCatalog();
    } catch (err) {
      toast.error('Erreur ajout pathologie');
    }
  },

  createAct: async (specialtyId, data) => {
    try {
      await api.post(`/catalog/specialties/${specialtyId}/acts`, data);
      toast.success('Acte ajouté');
      get().fetchCatalog();
    } catch (err) {
      toast.error('Erreur ajout acte');
    }
  },
}));
