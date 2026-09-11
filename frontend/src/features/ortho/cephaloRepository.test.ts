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
