import { api } from './api';
import type { Lab, LabJob, LabJobStatus } from '../types/labJob';

/** Fetch all LabJobs (active) from backend */
export const fetchLabJobs = async (): Promise<LabJob[]> => {
  const response = await api.get<LabJob[]>('/lab-jobs/');
  return response.data;
};

/** Patch LabJob status (or other fields) */
export const patchLabJobStatus = async (
  jobId: number,
  updates: Partial<Pick<LabJob, 'status'>>
): Promise<LabJob> => {
  const response = await api.patch<LabJob>(`/lab-jobs/${jobId}`, updates);
  return response.data;
};

/** Create a new LabJob manually */
export const createLabJob = async (
  jobData: Omit<LabJob, 'id' | 'status' | 'is_late' | 'created_at' | 'updated_at'> & { status?: LabJobStatus }
): Promise<LabJob> => {
  const response = await api.post<LabJob>('/lab-jobs/', jobData);
  return response.data;
};


export const fetchLabs = async (): Promise<Lab[]> => {
  const response = await api.get<Lab[]>('/lab-jobs/labs');
  return response.data;
};

export const createLab = async (data: Pick<Lab, 'name' | 'phone' | 'notes'>): Promise<Lab> => {
  const response = await api.post<Lab>('/lab-jobs/labs', data);
  return response.data;
};

export const deleteLab = async (labId: number): Promise<void> => {
  await api.delete(`/lab-jobs/labs/${labId}`);
};
