import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DashboardHeader } from './components/DashboardHeader';
import { QuickActions } from './components/QuickActions';
import { WaitingRoom } from './components/WaitingRoom';
import { IntelligenceAlerts } from './components/IntelligenceAlerts';
import { MarketplaceCard } from './components/MarketplaceCard';

afterEach(() => cleanup());

const healthy = {
  label: 'Opérationnel',
  dotClassName: 'bg-emerald-500',
  isLoading: false,
};

describe('Dashboard G2 interactive component matrix', () => {
  it('searches, closes search, navigates to a patient, and exposes permission-gated quick add actions', () => {
    const onNavigatePatient = vi.fn();
    const search = {
      isExpanded: true,
      query: 'benali',
      results: [{ id: 7, nom: 'Benali', prenom: 'Sara', numero_dossier: 'P-7' }],
      loading: false,
      open: vi.fn(),
      close: vi.fn(),
      change: vi.fn(),
    };

    render(
      <MemoryRouter>
        <DashboardHeader
          displayName="Dr Test"
          dateLabel="19 septembre 2026"
          canReadPatients
          canUseAgenda
          canAdmin
          systemStatus={healthy as never}
          search={search}
          onNavigatePatient={onNavigatePatient}
          onOpenMobile={vi.fn()}
          mobileButtonRef={{ current: null }}
        />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByRole('textbox', { name: 'Chercher un patient' }), { target: { value: 'sara' } });
    expect(search.change).toHaveBeenCalledWith('sara');

    fireEvent.click(screen.getByText('BENALI Sara'));
    expect(onNavigatePatient).toHaveBeenCalledWith(7);
    expect(search.close).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Ajout rapide' }));
    expect(screen.getByRole('menuitem', { name: /Nouveau Patient/i })).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: /Nouveau RDV/i })).toBeTruthy();
  });

  it('hides patient, agenda and admin dashboard controls when permissions do not allow them', () => {
    render(
      <MemoryRouter>
        <DashboardHeader
          displayName="Assistante"
          dateLabel="19 septembre 2026"
          canReadPatients={false}
          canUseAgenda={false}
          canAdmin={false}
          systemStatus={healthy as never}
          search={{ isExpanded: false, query: '', results: [], loading: false, open: vi.fn(), close: vi.fn(), change: vi.fn() }}
          onNavigatePatient={vi.fn()}
          onOpenMobile={vi.fn()}
          mobileButtonRef={{ current: null }}
        />
      </MemoryRouter>,
    );

    expect(screen.queryByRole('button', { name: 'Chercher un patient' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Ajout rapide' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Appairer le téléphone mobile' })).toBeNull();
    expect(screen.queryByText('Statut système')).toBeNull();
  });

  it('routes QuickActions only for authorized capabilities', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<QuickActions canReadPatients canUseAgenda={false} />} />
          <Route path="/patients/new" element={<div>New patient destination</div>} />
          <Route path="/patients" element={<div>Patient list destination</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.queryByText('Agenda Clinique')).toBeNull();
    fireEvent.click(screen.getByText('Nouveau Patient'));
    expect(screen.getByText('New patient destination')).toBeTruthy();
  });

  it('drives waiting-room state transitions through the supplied mutation boundary', () => {
    const onStatusChange = vi.fn();
    const onRefresh = vi.fn();
    const appointments = [
      { id: 1, start_time: '2026-09-19T09:00:00', status: 'PLANIFIÉ', description: 'Consultation', patient: { nom: 'A', prenom: 'One' } },
      { id: 2, start_time: '2026-09-19T10:00:00', status: 'EN_S_ATTENTE', description: '', patient: { nom: 'B', prenom: 'Two' } },
      { id: 3, start_time: '2026-09-19T11:00:00', status: 'EN_FAUTEUIL', description: '', patient: { nom: 'C', prenom: 'Three' } },
    ];

    render(
      <MemoryRouter>
        <WaitingRoom visible appointments={appointments as never} loading={false} onRefresh={onRefresh} onStatusChange={onStatusChange} />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: "Actualiser la file d'attente" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Marquer Arrivé' }));
    expect(onStatusChange).toHaveBeenCalledWith(1, 'EN_S_ATTENTE');

    fireEvent.click(screen.getByRole('button', { name: 'Installer au Fauteuil' }));
    expect(onStatusChange).toHaveBeenCalledWith(2, 'EN_FAUTEUIL');

    fireEvent.click(screen.getByRole('button', { name: 'Terminer la Séance' }));
    expect(onStatusChange).toHaveBeenCalledWith(3, 'TERMINÉ');
  });

  it('distinguishes unavailable waiting-room data from a truthful empty state', () => {
    const retry = vi.fn();
    const view = render(
      <MemoryRouter>
        <WaitingRoom visible appointments={null} loading={false} onRefresh={retry} onStatusChange={vi.fn()} />
      </MemoryRouter>,
    );

    expect(screen.getByText('Rendez-vous indisponibles')).toBeTruthy();
    expect(screen.queryByText("Aucun patient aujourd'hui")).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(retry).toHaveBeenCalled();

    view.unmount();
    render(
      <MemoryRouter>
        <WaitingRoom visible appointments={[]} loading={false} onRefresh={vi.fn()} onStatusChange={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Aucun patient aujourd'hui")).toBeTruthy();
  });

  it('executes proactive-alert patient navigation, snooze and mark-read actions independently', () => {
    const onNavigatePatient = vi.fn();
    const onSnooze = vi.fn();
    const onMarkRead = vi.fn();

    render(
      <IntelligenceAlerts
        forecast={null}
        alerts={[{ id: 12, patient_id: 7, priority: 1, nom: 'BENALI', prenom: 'Sara', title: 'Contrôle', action: 'Rappeler' } as never]}
        showForecast={false}
        showAlerts
        onNavigatePatient={onNavigatePatient}
        onSnooze={onSnooze}
        onMarkRead={onMarkRead}
      />,
    );

    fireEvent.click(screen.getByText(/BENALI Sara/));
    expect(onNavigatePatient).toHaveBeenCalledWith(7);

    fireEvent.click(screen.getByRole('button', { name: 'Reporter cette alerte de 24h' }));
    expect(onSnooze).toHaveBeenCalledWith(12);

    fireEvent.click(screen.getByRole('button', { name: 'Marquer cette alerte comme lue' }));
    expect(onMarkRead).toHaveBeenCalledWith(12);
  });

  it('routes the marketplace card only when patient access makes it visible', () => {
    const view = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<MarketplaceCard visible />} />
          <Route path="/approvisionnement" element={<div>Marketplace destination</div>} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByText('Commander les consommables et fournitures du cabinet'));
    expect(screen.getByText('Marketplace destination')).toBeTruthy();

    view.unmount();
    render(<MemoryRouter><MarketplaceCard visible={false} /></MemoryRouter>);
    expect(screen.queryByText('Commander les consommables et fournitures du cabinet')).toBeNull();
  });
});
