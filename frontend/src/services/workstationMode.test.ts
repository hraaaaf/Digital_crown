import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

import { api } from './api';
import { workstationModeService, type WorkstationState } from './workstationMode';

const state: WorkstationState = {
  workstationId: 'ws-serial-1',
  displayName: 'Accueil 1',
  defaultExperience: 'cabinet',
  stationLocked: false,
  stationEscapeAuthorized: false,
  pinConfigured: true,
  canManage: true,
  canConfigurePin: true,
  enrollmentRequired: false,
};

describe('workstationModeService state read serialization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shares one /workstation/state request across concurrent callers', async () => {
    let resolve!: (value: { data: WorkstationState }) => void;
    const pending = new Promise<{ data: WorkstationState }>((res) => { resolve = res; });
    vi.mocked(api.get).mockReturnValueOnce(pending as never);

    const first = workstationModeService.getState();
    const second = workstationModeService.getState();

    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenCalledWith('/workstation/state');

    resolve({ data: state });

    await expect(first).resolves.toEqual(state);
    await expect(second).resolves.toEqual(state);
  });

  it('starts a fresh request after the shared read settles', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: state } as never)
      .mockResolvedValueOnce({ data: { ...state, displayName: 'Accueil principal' } } as never);

    await workstationModeService.getState();
    const refreshed = await workstationModeService.getState();

    expect(api.get).toHaveBeenCalledTimes(2);
    expect(refreshed.displayName).toBe('Accueil principal');
  });
});
