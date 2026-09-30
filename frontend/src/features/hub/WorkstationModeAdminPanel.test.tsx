import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { WorkstationModeAdminPanel } from './WorkstationModeAdminPanel';
import { workstationModeService } from '../../services/workstationMode';

vi.mock('../../services/workstationMode', () => ({
  workstationModeService: {
    getBootstrapState: vi.fn(),
    getState: vi.fn(),
    configureOwnerPin: vi.fn(),
    changeMode: vi.fn(),
  },
}));

const baseState = {
  workstationId: 'ws-1',
  defaultExperience: null,
  stationLocked: false,
  stationEscapeAuthorized: false,
  pinConfigured: false,
  canManage: true,
  canConfigurePin: true,
};

describe('WorkstationModeAdminPanel V1.5-00.3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      ...baseState,
      authenticated: true,
    });
  });

  it('configures the owner PIN only from explicit owner credentials', async () => {
    vi.mocked(workstationModeService.getState)
      .mockResolvedValueOnce(baseState)
      .mockResolvedValueOnce({ ...baseState, pinConfigured: true });

    render(<MemoryRouter><WorkstationModeAdminPanel /></MemoryRouter>);

    await screen.findByText('Mode de démarrage permanent');
    fireEvent.click(screen.getByText('Configurer le PIN propriétaire'));
    fireEvent.change(screen.getByLabelText('Mot de passe du compte'), { target: { value: 'AccountPass!' } });
    fireEvent.change(screen.getByLabelText('Nouveau PIN'), { target: { value: '2468' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le PIN' }));

    await waitFor(() => expect(workstationModeService.configureOwnerPin).toHaveBeenCalledWith('AccountPass!', '2468'));
    await screen.findByText('PIN propriétaire enregistré.');
  });

  it('persists a selected permanent mode only with the owner PIN', async () => {
    vi.mocked(workstationModeService.getState).mockResolvedValue({
      ...baseState,
      pinConfigured: true,
      defaultExperience: 'cabinet',
    });
    vi.mocked(workstationModeService.changeMode).mockResolvedValue({
      ...baseState,
      pinConfigured: true,
      defaultExperience: 'station',
      stationLocked: true,
    });

    render(<MemoryRouter><WorkstationModeAdminPanel /></MemoryRouter>);

    await screen.findByText('Mode de démarrage permanent');
    fireEvent.click(screen.getByRole('button', { name: "Station d'accueil" }));
    fireEvent.change(screen.getByLabelText('PIN propriétaire'), { target: { value: '2468' } });
    fireEvent.click(screen.getByRole('button', { name: 'Appliquer ce mode' }));

    await waitFor(() => expect(workstationModeService.changeMode).toHaveBeenCalledWith('station', '2468'));
  });

  it('stays invisible and never calls protected state for a user who cannot manage workstation mode', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      ...baseState,
      authenticated: false,
      canManage: false,
      canConfigurePin: false,
    });
    const { container } = render(<MemoryRouter><WorkstationModeAdminPanel /></MemoryRouter>);
    await waitFor(() => expect(workstationModeService.getBootstrapState).toHaveBeenCalled());
    expect(workstationModeService.getState).not.toHaveBeenCalled();
    expect(container).toBeEmptyDOMElement();
  });
});
