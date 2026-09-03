import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const axiosPost = vi.fn();
const axiosGet = vi.fn();
const getPlatformToken = vi.fn();
const setPlatformToken = vi.fn();
const clearPlatformToken = vi.fn();

vi.mock('axios', () => ({
  default: {
    post: (...args: unknown[]) => axiosPost(...args),
    get: (...args: unknown[]) => axiosGet(...args),
  },
}));

vi.mock('../services/api', () => ({
  API_BASE: window.location.origin,
  PLATFORM_API_BASE: window.location.origin,
  getMobilePlatformAccessToken: () => getPlatformToken(),
  setMobilePlatformAccessToken: (token: string) => setPlatformToken(token),
  clearMobilePlatformAccessToken: () => clearPlatformToken(),
}));

vi.mock('../features/superadmin/SuperAdminAccessBoundary', () => ({
  SuperAdminAccessBoundary: () => <div data-testid="platform-workspace">Platform workspace</div>,
}));

import { MobileSuperAdminView } from '../features/mobile/Dashboard/views/MobileSuperAdminView';

beforeEach(() => {
  axiosPost.mockReset();
  axiosGet.mockReset();
  getPlatformToken.mockReset();
  setPlatformToken.mockReset();
  clearPlatformToken.mockReset();
  getPlatformToken.mockReturnValue(null);
  window.history.replaceState({}, '', '/mobile/superadmin');
});

describe('MobileSuperAdminView', () => {
  it('requires a separate same-origin platform login before exposing the workspace', async () => {
    const user = userEvent.setup();
    axiosPost.mockResolvedValueOnce({ data: { access_token: 'platform-access', refresh_token: 'discarded' } });
    axiosGet.mockResolvedValueOnce({
      data: {
        enrolled: true,
        step_up_valid: false,
        origin_ready: true,
        expected_origin: window.location.origin,
      },
    });

    render(<MemoryRouter><MobileSuperAdminView /></MemoryRouter>);

    expect(screen.getByTestId('mobile-superadmin-login')).toBeInTheDocument();
    expect(screen.queryByTestId('platform-workspace')).not.toBeInTheDocument();

    await user.type(screen.getByLabelText('Email plateforme'), 'OWNER@EXAMPLE.TEST');
    await user.type(screen.getByLabelText('Mot de passe'), 'correct horse battery staple');
    await user.click(screen.getByRole('button', { name: 'Ouvrir la Tour de contrôle' }));

    expect(await screen.findByTestId('platform-workspace')).toBeInTheDocument();
    expect(setPlatformToken).toHaveBeenCalledWith('platform-access');
    expect(axiosPost).toHaveBeenCalledWith(
      `${window.location.origin}/api/auth/login`,
      expect.any(URLSearchParams),
      expect.objectContaining({ withCredentials: true }),
    );
    expect(axiosGet).toHaveBeenCalledWith(
      `${window.location.origin}/api/superadmin/passkey/status`,
      expect.objectContaining({ headers: { Authorization: 'Bearer platform-access' }, withCredentials: true }),
    );
  });

  it('never persists a valid account that lacks platform authority', async () => {
    const user = userEvent.setup();
    axiosPost.mockResolvedValueOnce({ data: { access_token: 'ordinary-access' } });
    axiosGet.mockRejectedValueOnce({ response: { status: 403, data: { detail: 'denied' } } });

    render(<MemoryRouter><MobileSuperAdminView /></MemoryRouter>);
    await user.type(screen.getByLabelText('Email plateforme'), 'dentist@example.test');
    await user.type(screen.getByLabelText('Mot de passe'), 'password');
    await user.click(screen.getByRole('button', { name: 'Ouvrir la Tour de contrôle' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('autorité plateforme refusée');
    expect(setPlatformToken).not.toHaveBeenCalled();
    expect(screen.queryByTestId('platform-workspace')).not.toBeInTheDocument();
  });

  it('rejects a WebAuthn origin mismatch before persisting the platform session', async () => {
    const user = userEvent.setup();
    axiosPost.mockResolvedValueOnce({ data: { access_token: 'platform-access' } });
    axiosGet.mockResolvedValueOnce({
      data: {
        enrolled: true,
        step_up_valid: false,
        origin_ready: false,
        expected_origin: 'https://other-control.example.test',
      },
    });

    render(<MemoryRouter><MobileSuperAdminView /></MemoryRouter>);
    await user.type(screen.getByLabelText('Email plateforme'), 'owner@example.test');
    await user.type(screen.getByLabelText('Mot de passe'), 'password');
    await user.click(screen.getByRole('button', { name: 'Ouvrir la Tour de contrôle' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('https://other-control.example.test');
    expect(setPlatformToken).not.toHaveBeenCalled();
    expect(screen.queryByTestId('platform-workspace')).not.toBeInTheDocument();
  });

  it('restores only an existing dedicated platform session on the correct origin', () => {
    getPlatformToken.mockReturnValue('existing-platform-token');
    render(<MemoryRouter><MobileSuperAdminView /></MemoryRouter>);
    expect(screen.getByTestId('platform-workspace')).toBeInTheDocument();
    expect(screen.queryByTestId('mobile-superadmin-login')).not.toBeInTheDocument();
  });
});
