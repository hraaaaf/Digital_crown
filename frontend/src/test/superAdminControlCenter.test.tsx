import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiGet = vi.fn();
const apiPost = vi.fn();
const apiPatch = vi.fn();

vi.mock('../services/api', () => ({
  api: {
    get: (...args: unknown[]) => apiGet(...args),
    post: (...args: unknown[]) => apiPost(...args),
    patch: (...args: unknown[]) => apiPatch(...args),
  },
}));

vi.mock('../features/superadmin/platformPasskey', () => ({
  fetchPlatformPasskeyStatus: vi.fn(async () => ({
    enrolled: true,
    origin_ready: true,
    step_up_valid: true,
    rp_id: 'digitalcrown.local',
    expected_origin: 'https://digitalcrown.local',
  })),
  establishPlatformStepUp: vi.fn(async () => undefined),
}));

import { SuperAdminControlCenter } from '../features/superadmin/SuperAdminControlCenter';

beforeEach(() => {
  apiGet.mockReset();
  apiPost.mockReset();
  apiPatch.mockReset();
  apiGet.mockImplementation((url: string) => {
    if (url === '/superadmin/clients') {
      return Promise.resolve({ data: [{ id: 7, email: 'cabinet@example.com', nom_complet: 'Cabinet Test' }] });
    }
    if (url === '/superadmin/platform-admins/clients/7/devices') {
      return Promise.resolve({
        data: {
          client_id: 7,
          license: {
            active: true,
            license_type: 'PAID',
            max_devices: 3,
            active_devices: 1,
            release_channel: 'beta',
          },
          devices: [{ device_id: 'device-7', user_id: 7, active: true }],
        },
      });
    }
    if (url === '/superadmin/platform-admins') {
      return Promise.resolve({
        data: [{
          id: 1,
          email: 'owner@example.com',
          nom_complet: 'Owner',
          is_active: true,
          is_suspended: false,
          is_owner: true,
          permissions: { 'license.read': true, 'audit.read': true },
        }],
      });
    }
    if (url === '/superadmin/audit') {
      return Promise.resolve({
        data: [{
          id: 9,
          timestamp: '2026-08-31T10:00:00Z',
          user_id: 1,
          action: 'SUPERADMIN_RELEASE_CHANNEL_CHANGE',
          resource_type: 'User',
          resource_id: '7',
          severity: 'WARNING',
          details: 'from=stable;to=beta',
        }],
      });
    }
    return Promise.reject(new Error(`Unexpected GET ${url}`));
  });
});

describe('SuperAdminControlCenter', () => {
  it('surfaces devices, release channel, operators and audit from real API contracts', async () => {
    render(<SuperAdminControlCenter />);

    expect(await screen.findByTestId('superadmin-devices-panel')).toBeInTheDocument();
    expect(await screen.findByText('1/3')).toBeInTheDocument();
    expect(screen.getByText('beta', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByText('device-7')).toBeInTheDocument();

    expect(await screen.findByTestId('superadmin-operators-panel')).toBeInTheDocument();
    expect(await screen.findByText('owner@example.com')).toBeInTheDocument();

    expect(await screen.findByTestId('superadmin-audit-panel')).toBeInTheDocument();
    expect(await screen.findByText('SUPERADMIN_RELEASE_CHANNEL_CHANGE')).toBeInTheDocument();

    expect(screen.getByTestId('superadmin-release-channel')).toBeInTheDocument();
    expect(screen.getByTestId('superadmin-passkey-panel')).toBeInTheDocument();
  });
});
