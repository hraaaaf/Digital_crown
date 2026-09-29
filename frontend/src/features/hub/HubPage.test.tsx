import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { HubPage } from './HubPage';

const LocationProbe = () => { const location = useLocation(); return <div data-testid="location">{location.pathname}</div>; };

const renderHub = () => render(<MemoryRouter initialEntries={['/hub']}><HubPage/><LocationProbe/></MemoryRouter>);

describe('V1.5 HubPage', () => {
  beforeEach(() => { vi.resetAllMocks(); vi.stubGlobal('fetch', vi.fn()); });

  it('renders only the three workstation experiences without business data', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ nom_cabinet: 'Clinique Test', cabinet_type: 'CLINIQUE' }) } as Response);
    renderHub();
    expect(screen.getByText('Digital Crown')).toBeInTheDocument();
    expect(screen.getByText("Station d'accueil")).toBeInTheDocument();
    expect(screen.getByText('Centre de contrôle')).toBeInTheDocument();
    expect(screen.getByText('Le Hub ne contient aucune donnée patient ou clinique.')).toBeInTheDocument();
    await waitFor(() => { expect(screen.getByText('Clinique Test')).toBeInTheDocument(); expect(screen.getByText('CLINIQUE')).toBeInTheDocument(); });
  });

  it('stays usable when the cabinet backend is unavailable', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('offline'));
    renderHub();
    await waitFor(() => expect(screen.getByText(/Serveur indisponible/)).toBeInTheDocument());
    await userEvent.click(document.querySelector('[data-hub-experience="control"]') as HTMLButtonElement);
    expect(screen.getByTestId('location')).toHaveTextContent('/control-center');
  });

  it('routes Cabinet through the protected cabinet entry', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('offline'));
    renderHub();
    await userEvent.click(document.querySelector('[data-hub-experience="cabinet"]') as HTMLButtonElement);
    expect(screen.getByTestId('location')).toHaveTextContent('/cabinet');
  });
});
