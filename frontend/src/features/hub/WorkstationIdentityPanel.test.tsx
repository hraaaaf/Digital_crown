import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { WorkstationIdentityPanel } from './WorkstationIdentityPanel';
import { workstationModeService } from '../../services/workstationMode';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/workstationMode', () => ({
  workstationModeService: {
    listWorkstations: vi.fn(),
    issuePairingCode: vi.fn(),
    renameWorkstation: vi.fn(),
    revokeWorkstation: vi.fn(),
  },
}));

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: {
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
  },
}));

const current = {
  workstationId: 'ws-current-12345678',
  displayName: 'Accueil 1',
  defaultExperience: 'station' as const,
  stationLocked: true,
  stationEscapeAuthorized: false,
  pinConfigured: true,
  canManage: true,
  canConfigurePin: true,
};

const registry = [
  {
    workstationId: 'ws-current-12345678',
    displayName: 'Accueil 1',
    defaultExperience: 'station' as const,
    revoked: false,
    status: 'recent' as const,
    lastSeenAt: '2026-10-03T10:05:00',
    createdAt: '2026-10-03T10:00:00',
    updatedAt: '2026-10-03T10:00:00',
  },
  {
    workstationId: 'ws-other-87654321',
    displayName: 'Borne entrée',
    defaultExperience: 'station' as const,
    revoked: false,
    status: 'recent' as const,
    lastSeenAt: '2026-10-03T10:05:00',
    createdAt: '2026-10-03T10:00:00',
    updatedAt: '2026-10-03T10:00:00',
  },
];

describe('WorkstationIdentityPanel V1.5-03.2/03.3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workstationModeService.listWorkstations).mockResolvedValue(registry);
    vi.mocked(stationPatientSessionService.getConfig).mockResolvedValue({ fallbackMode: 'phone_dob' });
  });

  it('renames a station without changing its technical id', async () => {
    vi.mocked(workstationModeService.renameWorkstation).mockResolvedValue({
      workstationId: 'ws-current-12345678',
      displayName: 'Tablette secrétariat',
    });

    render(<WorkstationIdentityPanel current={current} />);
    await screen.findByText('Accueil 1');

    fireEvent.change(screen.getByLabelText('PIN propriétaire pour les actions sensibles'), {
      target: { value: '2468' },
    });
    fireEvent.change(screen.getByLabelText('Nom du poste', { selector: '#station-name-ws-current-12345678' }), {
      target: { value: 'Tablette secrétariat' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'Renommer' })[0]);

    await waitFor(() => expect(workstationModeService.renameWorkstation).toHaveBeenCalledWith(
      'ws-current-12345678',
      'Tablette secrétariat',
      '2468',
    ));
  });

  it('issues a single-use pairing code with owner PIN', async () => {
    vi.mocked(workstationModeService.issuePairingCode).mockResolvedValue({
      code: '654321',
      expiresAt: '2026-10-03T10:10:00',
    });

    render(<WorkstationIdentityPanel current={current} />);
    await screen.findByText('Accueil 1');

    fireEvent.change(screen.getByLabelText('PIN propriétaire pour les actions sensibles'), {
      target: { value: '2468' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Nouveau code d’appairage' }));

    expect(await screen.findByText('654321')).toBeInTheDocument();
    expect(screen.getByText('Usage unique · expiration automatique dans 10 minutes.')).toBeInTheDocument();
  });

  it('revokes the selected station explicitly', async () => {
    vi.mocked(workstationModeService.revokeWorkstation).mockResolvedValue(undefined);

    render(<WorkstationIdentityPanel current={current} />);
    await screen.findByText('Borne entrée');

    fireEvent.change(screen.getByLabelText('PIN propriétaire pour les actions sensibles'), {
      target: { value: '2468' },
    });
    fireEvent.click(screen.getAllByRole('button', { name: 'Révoquer' })[1]);
    expect(workstationModeService.revokeWorkstation).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la révocation' }));

    await waitFor(() => expect(workstationModeService.revokeWorkstation).toHaveBeenCalledWith(
      'ws-other-87654321',
      '2468',
    ));
  });

  it('configures Station fallback only with owner PIN', async () => {
    vi.mocked(stationPatientSessionService.updateConfig).mockResolvedValue({ fallbackMode: 'name_dob' });

    render(<WorkstationIdentityPanel current={current} />);
    await screen.findByText('Identification de secours Station');

    fireEvent.change(screen.getByLabelText('Méthode d’identification de secours'), {
      target: { value: 'name_dob' },
    });
    fireEvent.change(screen.getByLabelText('PIN propriétaire pour les actions sensibles'), {
      target: { value: '2468' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(stationPatientSessionService.updateConfig).toHaveBeenCalledWith('name_dob', '2468'));
    expect(await screen.findByRole('status')).toHaveTextContent('Identification de secours mise à jour');
  });
});
