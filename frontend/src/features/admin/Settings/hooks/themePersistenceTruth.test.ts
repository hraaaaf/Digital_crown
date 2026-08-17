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

const getMock = vi.mocked(api.get);
const putMock = vi.mocked(api.put);

describe('Settings branding theme persistence truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('digitalcrown_theme', 'elite');
    document.body.dataset.theme = '';
    document.documentElement.dataset.theme = '';
    useSettingsStore.setState({
      profile: {
        ...useSettingsStore.getState().profile,
        selected_theme: 'elite',
        primary_color: '#003380',
        secondary_color: '#1e40af',
        accent_color: '#60a5fa',
      },
      isDirty: false,
      saving: false,
      saveSuccess: false,
    });
  });

  it('previews a theme without persisting it before backend save', () => {
    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });

    expect(document.documentElement.dataset.theme).toBe('prestige');
    expect(localStorage.getItem('digitalcrown_theme')).toBe('elite');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });

  it('keeps the last persisted theme when backend save fails', async () => {
    putMock.mockRejectedValueOnce(new Error('backend unavailable'));
    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });

    await expect(useSettingsStore.getState().saveProfile()).rejects.toThrow('backend unavailable');

    expect(localStorage.getItem('digitalcrown_theme')).toBe('elite');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });

  it('persists the previewed theme only after backend save succeeds', async () => {
    putMock.mockResolvedValueOnce({ data: {} } as any);
    useSettingsStore.getState().updateProfile({ selected_theme: 'prestige' });

    await useSettingsStore.getState().saveProfile();

    expect(localStorage.getItem('digitalcrown_theme')).toBe('prestige');
    expect(useSettingsStore.getState().isDirty).toBe(false);
  });

  it('never overwrites the last persisted theme when profile fetch fails', async () => {
    localStorage.setItem('digitalcrown_theme', 'graphite');
    getMock.mockRejectedValueOnce(new Error('profile unavailable'));

    await useSettingsStore.getState().fetchProfile();

    expect(localStorage.getItem('digitalcrown_theme')).toBe('graphite');
  });

  it('persists the backend theme after a successful profile fetch', async () => {
    getMock.mockResolvedValueOnce({
      data: {
        nom_praticien: 'Dr Backend',
        nom_cabinet: 'Cabinet Backend',
        selected_theme: 'prestige',
        primary_color: '#003380',
        secondary_color: '#1e40af',
        accent_color: '#60a5fa',
        specialty_ids: [],
      },
    } as any);

    await useSettingsStore.getState().fetchProfile();

    expect(localStorage.getItem('digitalcrown_theme')).toBe('prestige');
  });
});
