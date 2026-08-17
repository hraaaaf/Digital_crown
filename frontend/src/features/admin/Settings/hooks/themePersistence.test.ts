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

describe('Settings theme persistence truth contract', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useSettingsStore.setState({
      profile: {
        ...useSettingsStore.getState().profile,
        selected_theme: 'elite',
        primary_color: '#003380',
        accent_color: '#60a5fa',
      },
      saving: false,
      saveSuccess: false,
      isDirty: false,
    });
  });

  it('previews a theme without overwriting the last persisted theme', () => {
    localStorage.setItem('digitalcrown_theme', 'elite');

    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });

    expect(document.documentElement.dataset.theme).toBe('prestige');
    expect(localStorage.getItem('digitalcrown_theme')).toBe('elite');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });

  it('commits the previewed theme only after a successful backend save', async () => {
    localStorage.setItem('digitalcrown_theme', 'elite');
    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });
    putMock.mockResolvedValueOnce({ data: {} } as any);

    await useSettingsStore.getState().saveProfile();

    expect(localStorage.getItem('digitalcrown_theme')).toBe('prestige');
    expect(useSettingsStore.getState().isDirty).toBe(false);
  });

  it('keeps the previously persisted theme when backend save fails', async () => {
    localStorage.setItem('digitalcrown_theme', 'elite');
    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });
    putMock.mockRejectedValueOnce(new Error('backend unavailable'));

    await expect(useSettingsStore.getState().saveProfile()).rejects.toThrow('backend unavailable');

    expect(document.documentElement.dataset.theme).toBe('prestige');
    expect(localStorage.getItem('digitalcrown_theme')).toBe('elite');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });
});
