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
    localStorage.clear();
    useSettingsStore.setState({
      profile: {
        ...useSettingsStore.getState().profile,
        performance_mode: false,
        clinical_tips_enabled: true,
        show_patient_badges: true,
      },
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

  it('sends practitioner and establishment INPE in the same backend write', async () => {
    putMock.mockResolvedValueOnce({ data: {} } as any);
    useSettingsStore.getState().updateProfile({
      inpe: 'PRO-42',
      inpe_etablissement: 'EST-42',
    });

    await useSettingsStore.getState().saveProfile();

    expect(putMock).toHaveBeenCalledTimes(1);
    expect(putMock).toHaveBeenCalledWith(
      '/clinics/me',
      expect.objectContaining({
        inpe: 'PRO-42',
        inpe_etablissement: 'EST-42',
      }),
    );
  });

  it('keeps runtime preferences staged until backend persistence succeeds', async () => {
    localStorage.setItem('performanceMode', 'false');
    putMock.mockResolvedValueOnce({ data: {} } as any);

    useSettingsStore.getState().updateProfile({ performance_mode: true });
    expect(localStorage.getItem('performanceMode')).toBe('false');
    expect(useSettingsStore.getState().isDirty).toBe(true);

    await useSettingsStore.getState().saveProfile();

    expect(localStorage.getItem('performanceMode')).toBe('true');
    expect(useSettingsStore.getState().isDirty).toBe(false);
  });

  it('never commits staged runtime preferences when backend persistence fails', async () => {
    localStorage.setItem('clinical_tips_enabled', 'true');
    putMock.mockRejectedValueOnce(new Error('backend unavailable'));

    useSettingsStore.getState().updateProfile({ clinical_tips_enabled: false });
    await expect(useSettingsStore.getState().saveProfile()).rejects.toThrow('backend unavailable');

    expect(localStorage.getItem('clinical_tips_enabled')).toBe('true');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });
});
