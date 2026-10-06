import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('./workstationMode', () => ({
  workstationModeService: {
    getBootstrapState: vi.fn(),
  },
}));

import axios from 'axios';
import { authService } from './auth';
import { workstationModeService } from './workstationMode';

describe('authService FUE quiet bootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('uses the 200 bootstrap probe when no local token exists', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId: null,
      defaultExperience: null,
      stationLocked: false,
      stationEscapeAuthorized: false,
      authenticated: false,
    });

    await expect(authService.isAuthenticated()).resolves.toBe(false);
    expect(workstationModeService.getBootstrapState).toHaveBeenCalledTimes(1);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('recognizes a cookie-backed authenticated session through bootstrap', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId: null,
      defaultExperience: null,
      stationLocked: false,
      stationEscapeAuthorized: false,
      authenticated: true,
    });

    await expect(authService.isAuthenticated()).resolves.toBe(true);
    expect(workstationModeService.getBootstrapState).toHaveBeenCalledTimes(1);
    expect(axios.get).not.toHaveBeenCalled();
  });
});
