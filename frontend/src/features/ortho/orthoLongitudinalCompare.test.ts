import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

import { api } from '../../services/api';
import {
  fetchOrthoCase,
  fetchOrthoLongitudinalCompare,
  fetchOrthoTimepoints,
} from './orthoLongitudinalCompare';

describe('orthoLongitudinalCompare F3 data contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the active/latest orthodontic case from the patient boundary', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { id: 12, patient_id: 915 } } as any);

    await fetchOrthoCase(915);

    expect(api.get).toHaveBeenCalledWith('/patients/915/ortho-case');
  });

  it('maps a missing orthodontic case to null without hiding other errors', async () => {
    vi.mocked(api.get).mockRejectedValueOnce({ response: { status: 404 } });

    await expect(fetchOrthoCase(915)).resolves.toBeNull();

    const error = { response: { status: 500 } };
    vi.mocked(api.get).mockRejectedValueOnce(error);
    await expect(fetchOrthoCase(915)).rejects.toBe(error);
  });

  it('loads canonical timepoints for the selected case', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] } as any);

    await fetchOrthoTimepoints(915, 12);

    expect(api.get).toHaveBeenCalledWith('/patients/915/ortho-case/12/timepoints');
  });

  it('requests a read-only numeric comparison with explicit ordinals', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: {} } as any);

    await fetchOrthoLongitudinalCompare(915, 12, 0, 2);

    expect(api.get).toHaveBeenCalledWith(
      '/patients/915/ortho-case/12/compare',
      { params: { from_ordinal: 0, to_ordinal: 2 } },
    );
  });
});
