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

export interface PractitionerIdentity {
  id: number;
  nom_complet: string;
  nom_complet_ar?: string | null;
  inpe_professionnel?: string | null;
}

export type CanonicalSetupPayload = CabinetConfigCreate & {
  nom?: string;
  inpe_etablissement?: string;
};

export type CanonicalCabinetDraft = CabinetConfig & {
  nom?: string;
  nom_praticien?: string;
  nom_praticien_ar?: string;
  inpe?: string;
  inpe_professionnel?: string | null;
  inpe_etablissement?: string | null;
  ice?: string;
  if_?: string;
  cabinet_type?: 'PRIVE' | 'CLINIQUE';
  specialty_ids?: string[];
  custom_specialty_fr?: string | null;
  custom_specialty_ar?: string | null;
  contacts_json?: Record<string, { enabled: boolean; value: string }>;
  selected_template?: string;
  margin_top?: number;
  margin_bottom?: number;
  header_scale?: number;
  header_font_scale?: number;
  header_logo_scale?: number;
  header_line_height?: number;
  footer_font_scale?: number;
  footer_qr_scale?: number;
  footer_line_height?: number;
  qr_code_enabled?: boolean;
  qr_code_type?: string;
  qr_code_value?: string | null;
  qr_code_color?: string | null;
  qr_code_label?: string | null;
  qr_code_style?: string;
  use_letterhead?: boolean;
};

// --- Cabinet API ---

export const cabinetApi = {
  /** Vérifier le statut d'initialisation du cabinet. */
  checkInitStatus: async (): Promise<CabinetInitStatus> => {
    const { data } = await api.get('/clinics/init-status');
    return data;
  },

  /** Lire l'identité canonique du praticien principal. */
  getPractitionerIdentity: async (): Promise<PractitionerIdentity> => {
    const { data } = await api.get('/clinics/me/practitioner');
    return data;
  },

  /** Enregistrer le brouillon canonique sans le déclarer initialisé. */
  create: async (config: CanonicalSetupPayload): Promise<CanonicalCabinetDraft> => {
    const { data } = await api.post('/clinics/', config);
    return data;
  },

  /** Finaliser l'installation après les opérations optionnelles réussies. */
  completeSetup: async (): Promise<CanonicalCabinetDraft> => {
    const { data } = await api.post('/clinics/complete-setup');
    return data;
  },

  /** Récupérer mon cabinet / brouillon via la façade canonique Settings. */
  getMine: async (): Promise<CanonicalCabinetDraft> => {
    const { data } = await api.get('/clinics/me');
    return data;
  },

  /** Mettre à jour mon cabinet. */
  update: async (config: Partial<CanonicalSetupPayload>): Promise<CanonicalCabinetDraft> => {
    const { data } = await api.put('/clinics/me', config);
    return data;
  },

  /** Uploader le logo. */
  uploadLogo: async (file: File): Promise<{ logo_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/clinics/me/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  /** Uploader le papier à en-tête (A5). */
  uploadLetterhead: async (file: File, marginsTop: number, marginsBottom: number): Promise<LetterheadUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('margins_top', marginsTop.toString());
    formData.append('margins_bottom', marginsBottom.toString());
    const { data } = await api.post('/clinics/me/letterhead', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};

export default {
  cabinet: cabinetApi,
};
