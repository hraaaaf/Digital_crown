import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from '../../pages/Dashboard';

const state = vi.hoisted(() => ({
  user: { role: 'ADMIN', nom_complet: 'Dr Test', permissions: {} as Record<string, boolean> },
  completedCb: null as null | ((patient: { nom: string; prenom: string }) => void),
}));

vi.mock('../../utils/accessControl', () => ({
  hasAccess: (_user: unknown, capability: string) => ['patients', 'agenda', 'accounting', 'admin'].includes(capability),
}));

vi.mock('../admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: (selector: (s: { profile: { show_patient_badges: boolean } }) => unknown) =>
    selector({ profile: { show_patient_badges: false } }),
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: () => ({ user: state.user, isLoading: false }),
}));

vi.mock('../../hooks/useCabinetHealth', () => ({
  useCabinetHealth: () => ({ status: 'healthy' }),
  getCabinetHealthDisplayState: () => ({ label: 'Opérationnel', dotClassName: 'bg-green-500', isLoading: false }),
}));

vi.mock('./hooks/useDashboardStats', () => ({
  useDashboardStats: () => ({ stats: {}, statsState: 'ready', praticienName: 'Dr Test', refreshStats: vi.fn() }),
}));
vi.mock('./hooks/useDashboardFinance', () => ({
  useDashboardFinance: () => ({
    forecast: { rdv_count: 2, forecast_revenue: 1000, avg_per_rdv: 500 },
    conversion: null,
    projection: null,
    latentCash: null,
    financeToday: null,
  }),
}));
vi.mock('./hooks/usePatientSearch', () => ({
  usePatientSearch: () => ({ isExpanded: false, query: '', results: [], loading: false, open: vi.fn(), close: vi.fn(), change: vi.fn() }),
}));
vi.mock('./hooks/useProactiveAlerts', () => ({
  useProactiveAlerts: () => ({ alerts: [], markRead: vi.fn(), snooze: vi.fn() }),
}));
vi.mock('./hooks/useTodayAppointments', () => ({
  useTodayAppointments: ({ onCompleted }: { onCompleted: (patient: { nom: string; prenom: string }) => void }) => {
    state.completedCb = onCompleted;
    return { appointments: [], loadingAppointments: false, refreshAppointments: vi.fn(), updateAppointmentStatus: vi.fn() };
  },
}));

vi.mock('./components/DashboardHeader', () => ({
  DashboardHeader: ({ onOpenMobile }: { onOpenMobile: () => void }) => (
    <button type="button" onClick={onOpenMobile}>Open mobile security</button>
  ),
}));
vi.mock('./components/QuickActions', () => ({ QuickActions: () => <div>Quick actions</div> }));
vi.mock('./components/WaitingRoom', () => ({ WaitingRoom: () => <div>Waiting room</div> }));
vi.mock('./components/RecentActivity', () => ({ RecentActivity: () => <div>Recent activity</div> }));
vi.mock('./components/IntelligenceAlerts', () => ({ IntelligenceAlerts: () => <div>Intelligence alerts</div> }));
vi.mock('./components/FinanceSummary', () => ({ FinanceSummary: () => <div>Finance summary</div> }));
vi.mock('./components/WeeklyPerformance', () => ({ WeeklyPerformance: () => <div>Weekly performance</div> }));
vi.mock('./components/BusinessInsights', () => ({ BusinessInsights: () => <div>Business insights</div> }));
vi.mock('./components/CabinetHealth', () => ({ CabinetHealth: () => <div>Cabinet health</div> }));
vi.mock('./components/MarketplaceCard', () => ({ MarketplaceCard: () => <div>Marketplace card</div> }));
vi.mock('../admin/Security/MobileSecurity', () => ({ MobileSecurity: () => <div>Mobile security content</div> }));

beforeEach(() => {
  vi.clearAllMocks();
  state.completedCb = null;
});

afterEach(() => cleanup());

describe('Dashboard G2 page orchestration matrix', () => {
  it('expands and collapses the management panel', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);

    const button = screen.getByRole('button', { name: /Pilotage du cabinet/i });
    expect(screen.queryByText('Finance summary')).toBeNull();

    fireEvent.click(button);
    expect(screen.getByText('Finance summary')).toBeTruthy();
    expect(screen.getByText('Weekly performance')).toBeTruthy();
    expect(screen.getByText('Business insights')).toBeTruthy();

    fireEvent.click(button);
    expect(screen.queryByText('Finance summary')).toBeNull();
  });

  it('opens and closes the mobile security dialog', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);

    fireEvent.click(screen.getByRole('button', { name: 'Open mobile security' }));
    expect(screen.getByRole('dialog', { name: 'Sécurité mobile' })).toBeTruthy();
    expect(screen.getByText('Mobile security content')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Fermer la fenêtre de sécurité mobile' }));
    expect(screen.queryByRole('dialog', { name: 'Sécurité mobile' })).toBeNull();
  });

  it('creates the discharge ghost checklist only after a completed appointment callback and closes explicitly', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);

    expect(screen.queryByText(/Patient Sortant/)).toBeNull();
    expect(state.completedCb).toBeTypeOf('function');

    state.completedCb!({ nom: 'BENALI', prenom: 'Sara' });

    expect(screen.getByText(/Patient Sortant : BENALI Sara/)).toBeTruthy();
    expect(screen.getByText('Encaisser les soins du jour')).toBeTruthy();
    expect(screen.getByText("Remettre l'ordonnance")).toBeTruthy();
    expect(screen.getByText('Fixer le RDV de contrôle')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Fermer les actions de sortie patient' }));
    expect(screen.queryByText(/Patient Sortant : BENALI Sara/)).toBeNull();
  });
});
