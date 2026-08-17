import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    promise: vi.fn(),
  },
}));

import { api } from '../../../../services/api';
import { useSettingsStore } from './useSettingsStore';

const putMock = vi.mocked(api.put);

describe('useSettingsStore saveProfile truth contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSettingsStore.setState({
      saving: false,
      saveSuccess: false,
      isDirty: true,
    });
  });

  it('rejects on backend failure and never exposes a positive saved state', async () => {
    putMock.mockRejectedValueOnce(new Error('backend unavailable'));

    await expect(useSettingsStore.getState().saveProfile()).rejects.toThrow('backend unavailable');

    const state = useSettingsStore.getState();
    expect(state.saving).toBe(false);
    expect(state.saveSuccess).toBe(false);
    expect(state.isDirty).toBe(true);
  });

  it('sets saved state only after a successful backend write', async () => {
    putMock.mockResolvedValueOnce({ data: {} } as any);

    await useSettingsStore.getState().saveProfile();

    const state = useSettingsStore.getState();
    expect(state.saving).toBe(false);
    expect(state.saveSuccess).toBe(true);
    expect(state.isDirty).toBe(false);
  });
});
