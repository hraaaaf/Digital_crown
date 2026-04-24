import { api } from './api';

export interface Point { 
  id: string; 
  x: number; 
  y: number; 
}

export interface AnalysisResults {
  analysis_id: number;
  results: {
    metrics: {
      analyse_osseuse: any;
      analyse_dentaire: any;
    };
    ai_narrative?: any;
    vision_metadata?: any;
    clinical_data?: any;
  };
  landmarks: Point[];
  file_url: string;
  is_calibrated: boolean;
  mm_per_pixel: number;
}

export interface AnalysisUpdate {
  landmarks: Point[];
  clinical_data?: any;
  ai_diagnostic?: any;
  mm_per_pixel?: number;
  mcnmara_projections?: any;
}

/**
 * Repository pour les analyses céphalométriques.
 * Centralise les interactions avec l'API /analyses.
 */
export const cephaloRepository = {
  /**
   * Téléverse une nouvelle radio et lance l'analyse IA initiale.
   */
  async uploadRadio(patientId: number, file: File): Promise<AnalysisResults> {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await api.post(`/patients/${patientId}/upload-radio`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      console.error(`[CephaloRepository] Erreur uploadRadio(${patientId}):`, error);
      throw error;
    }
  },

  /**
   * Met à jour une analyse avec de nouveaux points ou données cliniques.
   */
  async refineAnalysis(analysisId: number, data: AnalysisUpdate): Promise<AnalysisResults> {
    try {
      const response = await api.put(`/analyses/${analysisId}`, data);
      return response.data;
    } catch (error) {
      console.error(`[CephaloRepository] Erreur refineAnalysis(${analysisId}):`, error);
      throw error;
    }
  },

  /**
   * Calibre l'analyse (mm par pixel) via une distance connue.
   */
  async calibrate(analysisId: number, points: Point[], distanceMm: number) {
    try {
      const response = await api.post(`/analyses/${analysisId}/calibrate`, {
        points,
        distance_mm: distanceMm
      });
      return response.data;
    } catch (error) {
      console.error(`[CephaloRepository] Erreur calibrate(${analysisId}):`, error);
      throw error;
    }
  }
};
