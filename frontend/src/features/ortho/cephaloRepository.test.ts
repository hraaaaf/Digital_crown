import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

import { api } from '../../services/api';
import { cephaloRepository } from './cephaloRepository';
import { CLINICIAN_DIAGNOSTIC_ORIGIN } from './cephaloClinicalEvidence';

describe('cephaloRepository R1 calibration contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.post).mockResolvedValue({ data: { status: 'success' } } as any);
  });

  it('triggers auto-calibration without any client-selected physical profile', async () => {
    await cephaloRepository.autoCalibrate(41);

    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledWith('/ia/analyses/41/auto-calibrate', {});
    const body = vi.mocked(api.post).mock.calls[0][1] as Record<string, unknown>;
    expect(body).not.toHaveProperty('profile_id');
    expect(body).not.toHaveProperty('profile_version');
    expect(body).not.toHaveProperty('validation_reference');
  });

  it('confirms an already verified automatic calibration without resubmitting scale data', async () => {
    await cephaloRepository.confirmAutoCalibration(41);

    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledWith('/ia/analyses/41/auto-calibration/confirm', {});
  });
});

describe('cephaloRepository R15 clinical provenance boundary', () => {
  beforeEach(() => vi.clearAllMocks());

  it('does not expose unmarked historical diagnostic content as editable clinician content', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        id: 9,
        ai_diagnostic: { synthese_diagnostique: 'legacy' },
        angles_data: { ai_narrative: { diagnostic_squelettique: 'machine' }, metrics: {} },
      },
    } as any);

    const result = await cephaloRepository.getAnalysis(9);
    expect(result.ai_diagnostic).toBeNull();
    expect(result.angles_data.ai_narrative).toBeUndefined();
    expect(result.angles_data.__legacy_clinical_content).toBe('UNATTRIBUTED_LEGACY');
  });

  it('preserves explicitly marked clinician-authored diagnostic content', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        id: 10,
        ai_diagnostic: {
          _origin: CLINICIAN_DIAGNOSTIC_ORIGIN,
          analyse_dentaire: 'clinicien',
          diagnostic_squelettique: '',
          analyse_moulages: '',
          synthese_diagnostique: '',
          strategie_therapeutique: '',
        },
        angles_data: { metrics: {} },
      },
    } as any);

    const result = await cephaloRepository.getAnalysis(10);
    expect(result.ai_diagnostic._origin).toBe(CLINICIAN_DIAGNOSTIC_ORIGIN);
    expect(result.ai_diagnostic.analyse_dentaire).toBe('clinicien');
  });

  it('removes a fresh automated narrative before returning upload results to the store', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { analysis_id: 11, results: { ai_narrative: { synthese_diagnostique: 'machine' }, metrics: {} } },
    } as any);

    const result = await cephaloRepository.uploadRadio(7, new File(['x'], 'ceph.png'));
    expect(result.results.ai_narrative).toBeUndefined();
    expect(result.results.__legacy_clinical_content).toBe('UNATTRIBUTED_LEGACY');
  });
});
