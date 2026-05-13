// ==============================================================================
// SERVICES API MULTI-TENANT (Phase SaaS)
// ==============================================================================
import { api } from './api';
import type {
  CabinetConfig,
  CabinetConfigCreate,
  CabinetInitStatus,
  DocumentTemplate,
  DocumentTemplateList,
  DocumentTemplateCreate,
  DocumentTemplateUpdate,
  TemplatePreviewRequest,
  LetterheadUploadResponse,
  CardExtractionResult,
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

  /**
   * Extraire les infos d'une carte de visite (JPEG/PDF) via IA
   */
  extractCard: async (file: File): Promise<CardExtractionResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/clinics/extract-card', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};

// --- Templates API ---

export const templateApi = {
  /**
   * Récupérer tous les templates d'un cabinet
   */
  getByClinic: async (clinicId: string, type?: string): Promise<DocumentTemplateList[]> => {
    const { data } = await api.get(`/clinics/${clinicId}/templates`, {
      params: type ? { type } : undefined,
    });
    return data;
  },

  /**
   * Récupérer un template spécifique
   */
  getById: async (templateId: string): Promise<DocumentTemplate> => {
    const { data } = await api.get(`/templates/${templateId}`);
    return data;
  },

  /**
   * Créer un nouveau template (admin uniquement pour les templates système)
   */
  create: async (template: DocumentTemplateCreate): Promise<DocumentTemplate> => {
    const { data } = await api.post('/templates', template);
    return data;
  },

  /**
   * Mettre à jour un template (design_config uniquement)
   */
  update: async (templateId: string, updates: DocumentTemplateUpdate): Promise<DocumentTemplate> => {
    const { data } = await api.put(`/templates/${templateId}`, updates);
    return data;
  },

  /**
   * Supprimer un template personnalisé
   */
  delete: async (templateId: string): Promise<{ message: string }> => {
    const { data } = await api.delete(`/templates/${templateId}`);
    return data;
  },

  /**
   * Définir comme template par défaut
   */
  setDefault: async (templateId: string): Promise<{ message: string }> => {
    const { data } = await api.post(`/templates/${templateId}/set-default`);
    return data;
  },

  /**
   * Générer un PDF de prévisualisation
   * Retourne un Blob PDF
   */
  preview: async (request: TemplatePreviewRequest): Promise<Blob> => {
    const { data } = await api.post(`/templates/${request.template_id}/preview`, request, {
      responseType: 'blob',
    });
    return data;
  },
};

// Export combiné
export default {
  cabinet: cabinetApi,
  template: templateApi,
};
