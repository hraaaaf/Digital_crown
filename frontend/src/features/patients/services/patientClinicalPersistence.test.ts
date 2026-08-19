import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { patientClinicalPersistence } from './patientClinicalPersistence';

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const surfaces = {
  M: 'HEALTHY',
  D: 'HEALTHY',
  O: 'CARIES',
  V: 'HEALTHY',
  P: 'HEALTHY',
};

describe('patientClinicalPersistence', () => {
  beforeEach(() => vi.clearAllMocks());

  it('normalizes persisted odontogram tooth keys to numbers', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        id: 1,
        patient_id: 42,
        dentition_type: 'ADULT',
        state: { '11': surfaces },
        revision: 2,
        updated_by: 7,
        created_at: '2026-08-19T10:00:00',
        updated_at: '2026-08-19T10:01:00',
      },
    } as any);

    const result = await patientClinicalPersistence.getOdontogram(42);
    expect(api.get).toHaveBeenCalledWith('/patients/42/odontogram');
    expect(result?.state[11]?.O).toBe('CARIES');
    expect(result?.revision).toBe(2);
  });

  it('preserves optimistic revision on odontogram save', async () => {
    vi.mocked(api.put).mockResolvedValue({
      data: {
        id: 1,
        patient_id: 42,
        dentition_type: 'ADULT',
        state: { '11': surfaces },
        revision: 3,
        created_at: '2026-08-19T10:00:00',
        updated_at: '2026-08-19T10:02:00',
      },
    } as any);

    await patientClinicalPersistence.saveOdontogram(42, {
      dentition_type: 'ADULT',
      state: { 11: surfaces as any },
      expected_revision: 2,
    });

    expect(api.put).toHaveBeenCalledWith('/patients/42/odontogram', expect.objectContaining({ expected_revision: 2 }));
  });

  it('keeps practitioner conclusions on explicit POST only', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { id: 9, patient_id: 42, conclusion_text: 'Conclusion retenue', validated_by: 7, created_at: '2026-08-19T10:00:00' },
    } as any);

    await patientClinicalPersistence.createConclusion(42, {
      conclusion_text: 'Conclusion retenue',
      proposal_text: 'Proposition de questionnaire',
      proposal_source: 'Examen clinique complet',
    });

    expect(api.post).toHaveBeenCalledWith('/patients/42/clinical-conclusions', {
      conclusion_text: 'Conclusion retenue',
      proposal_text: 'Proposition de questionnaire',
      proposal_source: 'Examen clinique complet',
    });
  });

  it('reads Master Plan revision history without mutating it', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [{ id: 1, revision_number: 1 }] } as any);
    const revisions = await patientClinicalPersistence.listMasterPlanRevisions(42);
    expect(api.get).toHaveBeenCalledWith('/patients/42/master-plan/revisions');
    expect(revisions).toHaveLength(1);
  });
});
