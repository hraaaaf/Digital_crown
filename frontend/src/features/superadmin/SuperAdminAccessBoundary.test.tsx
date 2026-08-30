import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SuperAdminAccessBoundary } from './SuperAdminAccessBoundary';

const get = vi.fn();

vi.mock('../../services/api', () => ({
  api: { get },
}));

vi.mock('./SuperAdminDashboard', () => ({
  SuperAdminDashboard: () => <div>AUTHORIZED_SUPERADMIN_DASHBOARD</div>,
}));

vi.mock('../../components/DigitalCrownLoader', () => ({
  DigitalCrownLoader: () => <div>CHECKING_SUPERADMIN_ACCESS</div>,
}));

describe('SuperAdminAccessBoundary', () => {
  beforeEach(() => {
    get.mockReset();
  });

  it('renders only the neutral denied state after an authoritative 403', async () => {
    get.mockRejectedValue({ response: { status: 403 } });

    render(<SuperAdminAccessBoundary />);

    expect(await screen.findByText('Accès Superadmin non autorisé')).toBeInTheDocument();
    expect(screen.getByText('Votre session ne dispose pas d’une autorisation plateforme.')).toBeInTheDocument();
    expect(screen.queryByText('AUTHORIZED_SUPERADMIN_DASHBOARD')).not.toBeInTheDocument();
  });

  it('keeps an authorized backend session on the Superadmin dashboard', async () => {
    get.mockResolvedValue({ data: [] });

    render(<SuperAdminAccessBoundary />);

    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('AUTHORIZED_SUPERADMIN_DASHBOARD')).toBeInTheDocument();
    expect(screen.queryByText('Accès Superadmin non autorisé')).not.toBeInTheDocument();
  });
});
