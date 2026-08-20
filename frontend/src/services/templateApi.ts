// ==============================================================================
// SERVICES API MULTI-TENANT (Phase SaaS)
// ==============================================================================
import { api } from './api';
import type {
  CabinetConfig,
  CabinetConfigCreate,
  CabinetInitStatus,
  LetterheadUploadResponse,
} from '../types/template';

// --- Cabinet API ---

export const cabinetApi = {
  /**
   * Vérifier le statut d'initialisation du cabinet
   */
  checkInitStatus: async (): Promise<CabinetInitStatus> => {
    const { data } = await api.get('/clinics/init-status');
    return data;
  },

  /**
   * Créer un nouveau cabinet (Wizard étape 1)
   */
  create: async (config: CabinetConfigCreate): Promise<CabinetConfig> => {
    const { data } = await api.post('/clinics/', config);
    return data;
  },

  /**
   * Récupérer mon cabinet
   */
  getMine: async (): Promise<CabinetConfig> => {
    const { data } = await api.get('/clinics/me');
    return data;
  },

  /**
   * Mettre à jour mon cabinet
   */
  update: async (config: Partial<CabinetConfigCreate>): Promise<CabinetConfig> => {
    const { data } = await api.put('/clinics/me', config);
    return data;
  },

  /**
   * Uploader le logo
   */
  uploadLogo: async (file: File): Promise<{ logo_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post('/clinics/me/logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  /**
   * Uploader le papier à en-tête (A5)
   */
  uploadLetterhead: async (file: File, marginsTop: number, marginsBottom: number): Promise<LetterheadUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('margins_top', marginsTop.toString());
    formData.append('margins_bottom', marginsBottom.toString());

    const { data } = await api.post('/clinics/me/letterhead', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },
};

export default {
  cabinet: cabinetApi,
};
