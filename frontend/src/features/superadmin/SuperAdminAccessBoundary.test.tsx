import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SuperAdminAccessBoundary } from './SuperAdminAccessBoundary';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  api: { get: mocks.get },
}));

vi.mock('./SuperAdminWorkspace', () => ({
  SuperAdminWorkspace: () => <div>AUTHORIZED_SUPERADMIN_WORKSPACE</div>,
}));

vi.mock('../../components/DigitalCrownLoader', () => ({
  DigitalCrownLoader: () => <div>CHECKING_SUPERADMIN_ACCESS</div>,
}));

describe('SuperAdminAccessBoundary', () => {
  beforeEach(() => {
    mocks.get.mockReset();
  });

  it('renders only the neutral denied state after an authoritative 403', async () => {
    mocks.get.mockRejectedValue({ response: { status: 403 } });

    render(<SuperAdminAccessBoundary />);

    expect(await screen.findByText('Accès Superadmin non autorisé')).toBeInTheDocument();
    expect(screen.getByText('Votre session ne dispose pas d’une autorisation plateforme.')).toBeInTheDocument();
    expect(screen.queryByText('AUTHORIZED_SUPERADMIN_WORKSPACE')).not.toBeInTheDocument();
    expect(mocks.get).toHaveBeenCalledWith('/superadmin/passkey/status');
  });

  it('keeps an authorized backend session on the Superadmin workspace', async () => {
    mocks.get.mockResolvedValue({ data: { enrolled: true, step_up_valid: false } });

    render(<SuperAdminAccessBoundary />);

    await waitFor(() => expect(mocks.get).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('AUTHORIZED_SUPERADMIN_WORKSPACE')).toBeInTheDocument();
    expect(screen.queryByText('Accès Superadmin non autorisé')).not.toBeInTheDocument();
    expect(mocks.get).toHaveBeenCalledWith('/superadmin/passkey/status');
  });
});
