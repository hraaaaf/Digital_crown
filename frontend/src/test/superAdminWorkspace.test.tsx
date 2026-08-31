import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

let requestInterceptor: ((config: { method?: string; url?: string }) => Promise<unknown>) | null = null;
const interceptorUse = vi.fn();
const interceptorEject = vi.fn();
const fetchPlatformPasskeyStatus = vi.fn();
const establishPlatformStepUp = vi.fn();

vi.mock('../services/api', () => ({
  api: {
    interceptors: {
      request: {
        use: (...args: unknown[]) => interceptorUse(...args),
        eject: (...args: unknown[]) => interceptorEject(...args),
      },
    },
  },
}));

vi.mock('../features/superadmin/platformPasskey', () => ({
  fetchPlatformPasskeyStatus: (...args: unknown[]) => fetchPlatformPasskeyStatus(...args),
  establishPlatformStepUp: (...args: unknown[]) => establishPlatformStepUp(...args),
}));

vi.mock('../features/superadmin/SuperAdminControlCenter', () => ({
  SuperAdminControlCenter: () => <div data-testid="control-center">Control center</div>,
}));

vi.mock('../features/superadmin/SuperAdminDashboard', () => ({
  SuperAdminDashboard: () => <div data-testid="legacy-dashboard">Legacy dashboard</div>,
}));

import { SuperAdminWorkspace } from '../features/superadmin/SuperAdminWorkspace';

beforeEach(() => {
  requestInterceptor = null;
  interceptorUse.mockReset();
  interceptorEject.mockReset();
  fetchPlatformPasskeyStatus.mockReset();
  establishPlatformStepUp.mockReset();
  interceptorUse.mockImplementation((handler: typeof requestInterceptor) => {
    requestInterceptor = handler;
    return 17;
  });
});

describe('SuperAdminWorkspace', () => {
  it('opens the control center by default while preserving the legacy dashboard tab', async () => {
    const user = userEvent.setup();
    const { unmount } = render(<SuperAdminWorkspace />);

    expect(screen.getByTestId('control-center')).toBeInTheDocument();
    expect(screen.queryByTestId('legacy-dashboard')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Clients & licences' }));
    expect(screen.getByTestId('legacy-dashboard')).toBeInTheDocument();

    unmount();
    expect(interceptorEject).toHaveBeenCalledWith(17);
  });

  it('establishes step-up before legacy mutations but never intercepts passkey ceremonies', async () => {
    fetchPlatformPasskeyStatus.mockResolvedValue({ enrolled: true, step_up_valid: false });
    establishPlatformStepUp.mockResolvedValue(undefined);
    render(<SuperAdminWorkspace />);

    expect(requestInterceptor).not.toBeNull();
    await requestInterceptor?.({ method: 'post', url: '/superadmin/clients/42/grant-license' });
    expect(fetchPlatformPasskeyStatus).toHaveBeenCalledTimes(1);
    expect(establishPlatformStepUp).toHaveBeenCalledWith(true);

    fetchPlatformPasskeyStatus.mockClear();
    establishPlatformStepUp.mockClear();
    await requestInterceptor?.({ method: 'post', url: '/superadmin/passkey/authentication/options' });
    expect(fetchPlatformPasskeyStatus).not.toHaveBeenCalled();
    expect(establishPlatformStepUp).not.toHaveBeenCalled();
  });

  it('reuses a valid server step-up without launching WebAuthn again', async () => {
    fetchPlatformPasskeyStatus.mockResolvedValue({ enrolled: true, step_up_valid: true });
    render(<SuperAdminWorkspace />);

    await requestInterceptor?.({ method: 'patch', url: '/superadmin/clients/42/suspend' });
    expect(fetchPlatformPasskeyStatus).toHaveBeenCalledTimes(1);
    expect(establishPlatformStepUp).not.toHaveBeenCalled();
  });
});
