import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import { WorkstationModeGate } from './WorkstationModeGate';
import { workstationModeService } from '../../services/workstationMode';

vi.mock('../../services/workstationMode', () => ({
  workstationModeService: {
    getBootstrapState: vi.fn(),
    getState: vi.fn(),
    subscribe: vi.fn(() => () => undefined),
  },
}));

const bootstrap = {
  workstationId: 'ws-1',
  defaultExperience: 'station' as const,
  stationLocked: true,
  stationEscapeAuthorized: false,
};

const renderGate = (path: string, target: 'hub' | 'station' | 'control-center' | 'protected') => render(
  <MemoryRouter initialEntries={[path]}>
    <Routes>
      <Route path={path} element={<WorkstationModeGate target={target}><div>REQUESTED</div></WorkstationModeGate>} />
      <Route path="/station" element={<div>STATION</div>} />
      <Route path="/hub" element={<div>HUB</div>} />
    </Routes>
  </MemoryRouter>,
);

describe('WorkstationModeGate V1.5-00.3 direct URL security', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('blocks a direct Cabinet URL while Station is locked', async () => {
    vi.mocked(workstationModeService.getState).mockResolvedValue({
      ...bootstrap,
      pinConfigured: true,
      canManage: true,
      canConfigurePin: true,
    });
    renderGate('/dashboard', 'protected');
    await waitFor(() => expect(screen.getByText('STATION')).toBeInTheDocument());
    expect(screen.queryByText('REQUESTED')).not.toBeInTheDocument();
  });

  it('allows Cabinet only after server-authorized Station escape for the current user', async () => {
    vi.mocked(workstationModeService.getState).mockResolvedValue({
      ...bootstrap,
      stationEscapeAuthorized: true,
      pinConfigured: true,
      canManage: true,
      canConfigurePin: true,
    });
    renderGate('/dashboard', 'protected');
    await waitFor(() => expect(screen.getByText('REQUESTED')).toBeInTheDocument());
  });

  it('blocks direct Control Center navigation while Station is locked', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue(bootstrap);
    renderGate('/control-center', 'control-center');
    await waitFor(() => expect(screen.getByText('STATION')).toBeInTheDocument());
  });

  it('keeps Control Center available as the fail-soft recovery surface when workstation authority is unavailable', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockRejectedValue(new Error('backend unavailable'));
    renderGate('/control-center', 'control-center');
    await waitFor(() => expect(screen.getByText('REQUESTED')).toBeInTheDocument());
    expect(screen.queryByText('HUB')).not.toBeInTheDocument();
  });

  it('keeps the restrictive Station shell in place when workstation authority is unavailable', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockRejectedValue(new Error('backend unavailable'));
    renderGate('/station', 'station');
    await waitFor(() => expect(screen.getByText('REQUESTED')).toBeInTheDocument());
    expect(screen.queryByText('HUB')).not.toBeInTheDocument();
  });

  it('does not authorize Station by direct URL on an unconfigured workstation', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId: 'ws-1',
      defaultExperience: null,
      stationLocked: false,
      stationEscapeAuthorized: false,
    });
    renderGate('/station', 'station');
    await waitFor(() => expect(screen.getByText('HUB')).toBeInTheDocument());
  });

  it('revalidates an already mounted Cabinet tab when another tab changes the workstation mode', async () => {
    let notify: (() => void) | undefined;
    vi.mocked(workstationModeService.subscribe).mockImplementation((listener) => {
      notify = listener;
      return () => undefined;
    });
    vi.mocked(workstationModeService.getState)
      .mockResolvedValueOnce({
        ...bootstrap,
        defaultExperience: 'cabinet',
        stationLocked: false,
        stationEscapeAuthorized: false,
        pinConfigured: true,
        canManage: true,
        canConfigurePin: true,
        enrollmentRequired: false,
      })
      .mockResolvedValue({
        ...bootstrap,
        pinConfigured: true,
        canManage: true,
        canConfigurePin: true,
        enrollmentRequired: false,
      });

    renderGate('/dashboard', 'protected');
    await waitFor(() => expect(screen.getByText('REQUESTED')).toBeInTheDocument());

    await act(async () => {
      notify?.();
    });

    await waitFor(() => expect(screen.getByText('STATION')).toBeInTheDocument());
    expect(screen.queryByText('REQUESTED')).not.toBeInTheDocument();
  });
  it('revalidates an authorized owner escape before switching from Station to Hub', async () => {
    let escapeAuthorized = false;
    vi.mocked(workstationModeService.getBootstrapState).mockImplementation(async () => ({
      ...bootstrap,
      stationEscapeAuthorized: escapeAuthorized,
      stationEscapeExpiresAt: escapeAuthorized ? Math.floor(Date.now() / 1000) + 600 : null,
    }));

    const StationExit = () => {
      const navigate = useNavigate();
      return <button onClick={() => {
        escapeAuthorized = true;
        navigate('/hub?select=1', { replace: true });
      }}>Autoriser le Hub</button>;
    };

    render(
      <MemoryRouter initialEntries={['/station']}>
        <Routes>
          <Route path="/station" element={
            <WorkstationModeGate target="station"><StationExit /></WorkstationModeGate>
          } />
          <Route path="/hub" element={
            <WorkstationModeGate target="hub"><div>HUB APRÈS AUTORISATION</div></WorkstationModeGate>
          } />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByRole('button', { name: 'Autoriser le Hub' }));
    await screen.findByText('HUB APRÈS AUTORISATION');
    expect(workstationModeService.getBootstrapState).toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Autoriser le Hub' })).not.toBeInTheDocument();
  });

  it('fails closed for protected Cabinet routes if workstation authority is offline', async () => {
    vi.mocked(workstationModeService.getState).mockRejectedValue(new Error('offline'));
    renderGate('/dashboard', 'protected');
    await waitFor(() => expect(screen.getByText('HUB')).toBeInTheDocument());
    expect(screen.queryByText('REQUESTED')).not.toBeInTheDocument();
  });

  it('dispatches a configured Hub to the server-remembered Cabinet experience', async () => {
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId: 'ws-cabinet',
      defaultExperience: 'cabinet',
      stationLocked: false,
      stationEscapeAuthorized: false,
    });
    render(
      <MemoryRouter initialEntries={['/hub']}>
        <Routes>
          <Route path="/hub" element={
            <WorkstationModeGate target="hub"><div>HUB</div></WorkstationModeGate>
          } />
          <Route path="/cabinet" element={<div>REMEMBERED CABINET</div>} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText('REMEMBERED CABINET');
    expect(screen.queryByText('HUB')).not.toBeInTheDocument();
  });

});
