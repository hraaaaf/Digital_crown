import { create } from 'zustand';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';

export interface CatalogAct { id: number; specialty_id: number; name: string; code?: string; base_price: number; color?: string; is_active: boolean; }
export interface Pathology { id: number; specialty_id: number; name: string; description?: string; is_active: boolean; }
export interface Specialty { id: number; name: string; color?: string; pathologies: Pathology[]; acts: CatalogAct[]; }

interface CatalogState {
  specialties: Specialty[];
  loading: boolean;
  readError: string | null;
  fetchCatalog: () => Promise<void>;
  createSpecialty: (data: { name: string; color?: string }) => Promise<void>;
  updateSpecialty: (id: number, data: { name?: string; color?: string }) => Promise<void>;
  createPathology: (specialtyId: number, data: { name: string; description?: string }) => Promise<void>;
  createAct: (specialtyId: number, data: { name: string; base_price: number; code?: string; color?: string }) => Promise<void>;
  updateAct: (actId: number, data: { name?: string; base_price?: number; code?: string; is_active?: boolean }) => Promise<void>;
}

export const useCatalogStore = create<CatalogState>((set, get) => ({
  specialties: [], loading: false, readError: null,

  fetchCatalog: async () => {
    set({ loading: true, readError: null });
    try {
      const res = await api.get('/catalog/specialties');
      set({ specialties: res.data, readError: null });
    } catch (err) {
      console.error(err);
      set({ readError: "Impossible de charger le catalogue réel du cabinet. Aucune modification n'est autorisée tant que la lecture n'a pas réussi." });
      toast.error('Erreur lors du chargement du catalogue');
    } finally { set({ loading: false }); }
  },

  createSpecialty: async (data) => {
    if (get().readError) return;
    try { await api.post('/catalog/specialties', data); toast.success('Spécialité ajoutée'); await get().fetchCatalog(); }
    catch { toast.error('Erreur ajout spécialité'); }
  },
  updateSpecialty: async (id, data) => {
    if (get().readError) return;
    try { await api.put(`/catalog/specialties/${id}`, data); toast.success('Spécialité modifiée'); await get().fetchCatalog(); }
    catch { toast.error('Erreur modification spécialité'); }
  },
  createPathology: async (specialtyId, data) => {
    if (get().readError) return;
    try { await api.post(`/catalog/specialties/${specialtyId}/pathologies`, data); toast.success('Pathologie ajoutée'); await get().fetchCatalog(); }
    catch { toast.error('Erreur ajout pathologie'); }
  },
  createAct: async (specialtyId, data) => {
    if (get().readError) return;
    try { await api.post(`/catalog/specialties/${specialtyId}/acts`, data); toast.success('Acte ajouté'); await get().fetchCatalog(); }
    catch { toast.error('Erreur ajout acte'); }
  },
  updateAct: async (actId, data) => {
    if (get().readError) return;
    try { await api.put(`/catalog/acts/${actId}`, data); toast.success('Acte modifié'); await get().fetchCatalog(); }
    catch { toast.error('Erreur modification acte'); }
  },
}));
