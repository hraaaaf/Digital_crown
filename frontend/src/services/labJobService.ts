import { api } from './api';
import type { LabJob, LabJobStatus } from '../types/labJob';

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
