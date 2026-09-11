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
    const res = await api.get(`/ia/analyses/${analysisId}`);
    return res.data;
  },

  /**
   * Upload une radiographie et lance l'analyse géométrique automatique.
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
   * Demande au serveur de vérifier le candidat fiducial déjà persisté.
   * Aucun profil physique n'est sélectionnable côté client.
   */
  async autoCalibrate(analysisId: number) {
    const res = await api.post(`/ia/analyses/${analysisId}/auto-calibrate`, {});
    return res.data;
  },

  /**
   * Confirme facultativement une auto-calibration déjà AUTO_VERIFIED.
   */
  async confirmAutoCalibration(analysisId: number) {
    const res = await api.post(`/ia/analyses/${analysisId}/auto-calibration/confirm`, {});
    return res.data;
  },

  /**
   * Applique une calibration mm/pixel manuelle auditée sur une analyse.
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
   * Génère le rapport PDF complet.
   */
  async generatePDF(patientId: number | string, payload: any) {
    const res = await api.post(`/patients/${patientId}/pdf`, payload, { 
      responseType: 'blob' as any
    });
    return res.data;
  }
};
