/**
 * RVG (Intra-oral X-ray) service
 * Handles upload, listing, and deletion of patient RVG documents.
 */
import { api } from './api';

export interface RVGDocument {
  id: number;
  patient_id: number;
  document_type: string;
  original_filename?: string;
  download_url: string;
  tags?: string[];
  clinical_data?: {
    radio_type?: string;
    tooth_number?: string;
    sector?: string;
    acquisition_date?: string;
    note?: string;
  };
  created_at: string;
  uploaded_by_id?: number;
}

export interface RVGUploadRequest {
  file: File;
  radio_type?: 'rvg' | 'periapical' | 'bitewing' | 'occlusal' | 'other';
  tooth_number?: string;
  sector?: string;
  acquisition_date?: string;
  note?: string;
}

export const rvgService = {
  /**
   * Upload a new RVG to a patient's file.
   * Returns the created DocumentArchive entry.
   */
  async uploadRVG(patientId: number, request: RVGUploadRequest): Promise<RVGDocument> {
    const formData = new FormData();
    formData.append('file', request.file);
    if (request.radio_type) formData.append('radio_type', request.radio_type);
    if (request.tooth_number) formData.append('tooth_number', request.tooth_number);
    if (request.sector) formData.append('sector', request.sector);
    if (request.acquisition_date) formData.append('acquisition_date', request.acquisition_date);
    if (request.note) formData.append('note', request.note);

    const response = await api.post<RVGDocument>(
      `/documents/patients/${patientId}/rvg`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  /**
   * List all RVG documents for a patient.
   */
  async listRVG(patientId: number): Promise<RVGDocument[]> {
    const response = await api.get<RVGDocument[]>(`/documents/patients/${patientId}/rvg`);
    return response.data;
  },

  /**
   * Delete an RVG document (permanent delete via DocumentArchive).
   */
  async deleteRVG(documentId: number): Promise<void> {
    await api.delete(`/documents/${documentId}`, { params: { confirm: true } });
  },

  /**
   * Get download URL for an RVG (authenticated).
   * This URL should be used with AuthImg/useAuthenticatedImage.
   */
  getDownloadUrl(documentId: number, token?: string): string {
    if (token) {
      return `/api/documents/${documentId}/download?token=${token}`;
    }
    return `/api/documents/${documentId}/download`;
  },
};

export default rvgService;
