import { api } from '../../services/api';
import type { LabReviewClient } from './StaffReviewLab';

// Only the existing LAB backend routes; they fail closed outside isolated TEST.
// Do not use this adapter to mount a production route or claim clinical success.
export const labStaffHttpClient: LabReviewClient = {
  review: async (input) =>
    (await api.post('/imaging-acquisitions/lab/review', input)).data,
  approve: async (input) =>
    (await api.post('/imaging-acquisitions/lab/approve', input)).data,
};
