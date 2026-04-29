import { api } from '../../services/api';


/**
 * Repository central pour la gestion des analyses céphalométriques.
 * Centralise les appels API pour assurer la cohérence des données.
 */
export const cephaloRepository = {
  
  /**
   * Récupère une analyse existante par son ID.
   */
  async getAnalysis(analysisId: number) {
    const res = await api.get(`/analyses/${analysisId}`);
    return res.data;
  },

  /**
   * Upload une radiographie et lance l'analyse IA automatique.
   */
  async uploadRadio(patientId: number | string, file: File) {
    const form = new FormData();
    form.append('file', file);
    const res = await api.post(`/ia/upload-radio?patient_id=${patientId}`, form);
    return res.data;
  },

  /**
   * Sauvegarde l'état complet d'une analyse.
   */
  async saveAnalysis(analysisId: number, payload: any) {
    const res = await api.put(`/ia/analyses/${analysisId}`, payload);
    return res.data;
  },

  /**
   * Applique une calibration mm/pixel sur une analyse.
   */
  async calibrate(analysisId: number, p1: {x: number, y: number}, p2: {x: number, y: number}, distanceMm: number) {
    const res = await api.post(`/ia/analyses/${analysisId}/calibrate`, {
      p1, 
      p2, 
      distance_mm: distanceMm
    });
    return res.data;
  },

  /**
   * Récupère un diagnostic généré par l'IA (SLM/Ollama).
   */
  async getAIDiagnostic(patientId: number | string) {
    const res = await api.get(`/patients/${patientId}/ai-diagnostic`);
    return res.data?.report ?? res.data ?? {};
  },

  /**
   * Génère le rapport PDF complet.
   */
  async generatePDF(patientId: number | string, payload: any) {
    const res = await api.post(`/patients/${patientId}/pdf`, payload, { 
      responseType: 'blob' as any 
    });
    return res.data;
  }
};
