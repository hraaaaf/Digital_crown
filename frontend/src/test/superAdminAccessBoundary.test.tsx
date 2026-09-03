import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiGet = vi.fn();

vi.mock('../services/api', () => ({
  api: { get: (...args: unknown[]) => apiGet(...args) },
}));

vi.mock('../features/superadmin/SuperAdminWorkspace', () => ({
  SuperAdminWorkspace: () => <div data-testid="authorized-workspace">Authorized workspace</div>,
}));

import { SuperAdminAccessBoundary } from '../features/superadmin/SuperAdminAccessBoundary';

beforeEach(() => {
  apiGet.mockReset();
});

describe('SuperAdminAccessBoundary', () => {
  it('fails closed on an authoritative platform 403', async () => {
    apiGet.mockRejectedValueOnce({ response: { status: 403 } });

    render(<SuperAdminAccessBoundary />);

    expect(await screen.findByText('Accès Superadmin non autorisé')).toBeInTheDocument();
    expect(screen.queryByTestId('authorized-workspace')).not.toBeInTheDocument();
    expect(apiGet).toHaveBeenCalledWith('/superadmin/passkey/status');
  });

  it('fails closed when the control-plane cannot be verified', async () => {
    apiGet.mockRejectedValueOnce(new Error('network down'));

    render(<SuperAdminAccessBoundary />);

    expect(await screen.findByText('Control-plane indisponible')).toBeInTheDocument();
    expect(screen.queryByTestId('authorized-workspace')).not.toBeInTheDocument();
  });

  it('admits an explicitly authorized platform actor without requiring license.read', async () => {
    apiGet.mockResolvedValueOnce({ data: { enrolled: true, step_up_valid: false } });

    render(<SuperAdminAccessBoundary />);

    expect(await screen.findByTestId('authorized-workspace')).toBeInTheDocument();
    expect(screen.queryByText('Accès Superadmin non autorisé')).not.toBeInTheDocument();
    expect(apiGet).toHaveBeenCalledWith('/superadmin/passkey/status');
  });
});
