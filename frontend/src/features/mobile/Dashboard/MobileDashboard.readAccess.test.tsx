import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DENY_POCKET_READ, type PocketReadAccess } from './pocketReadCapabilities';

const mocks = vi.hoisted(() => ({
  access: { agenda: true, patients: true, clinical: false, finance: false },
  status: 'ready', tab: 'finance', finance: vi.fn(), patients: vi.fn(), refresh: vi.fn(),
}));
vi.mock('./hooks/usePocketReadCapabilities', () => ({ usePocketReadCapabilities: () => ({ access: mocks.access, status: mocks.status, refresh: mocks.refresh }) }));
vi.mock('./hooks/useMobileRuntimeTheme', () => ({ useMobileRuntimeTheme: vi.fn() }));
vi.mock('./hooks/useMobileQuickActionCapabilities', () => ({ useMobileQuickActionCapabilities: () => ({ capabilities: { can_create_appointment: true, can_create_patient: true, can_open_clinical_context: true, can_pay: false }, loaded: true, refresh: vi.fn() }) }));
vi.mock('./hooks/useMobileDashboard', () => ({ useMobileDashboard: () => ({
  state: { activeTab: mocks.tab, snapshot: { generated_at: 'synthetic', role: 'SECRETAIRE', appointments: [] }, selectedDate: '2026-10-12', syncStatus: 'success', queuedActionsCount: 0, isOnline: true },
  actions: { setActiveTab: vi.fn(), setSelectedDate: vi.fn(), fetchSnapshot: vi.fn() }, refs: { mainRef: { current: null } },
}) }));
vi.mock('./views/FinanceView', () => ({ FinanceView: () => { mocks.finance(); return <div>Finance réellement montée</div>; } }));
vi.mock('./views/MobilePatientsGate', () => ({ MobilePatientsGate: () => { mocks.patients(); return <div>Dossiers réellement montés</div>; } }));
vi.mock('./components/MobileNotificationCenter', () => ({ MobileNotificationCenter: () => <div>Notifications autorisées</div> }));
vi.mock('../../../components/PWAInstallPrompt', () => ({ PWAInstallPrompt: () => null }));
import { MobileDashboard } from './MobileDashboard';

const shell = () => <MemoryRouter initialEntries={['/mobile/dashboard?tab=' + mocks.tab]}><MobileDashboard /></MemoryRouter>;
beforeEach(() => {
  vi.clearAllMocks();
  mocks.access = { agenda: true, patients: true, clinical: false, finance: false };
  mocks.status = 'ready'; mocks.tab = 'finance';
});
afterEach(cleanup);

describe('Pocket runtime read guards', () => {
  it('blocks a finance deep link before mounting data, including for a loaded staff profile', () => {
    render(shell());
    expect(screen.getByText('Accès réservé')).toBeTruthy();
    expect(mocks.finance).not.toHaveBeenCalled();
  });
  it('allows secretary finance by permission and removes the open screen when revoked', () => {
    mocks.access.finance = true;
    const { rerender } = render(shell());
    expect(screen.getByText('Finance réellement montée')).toBeTruthy();
    mocks.access = { ...mocks.access, finance: false };
    rerender(shell());
    expect(screen.queryByText('Finance réellement montée')).toBeNull();
    expect(screen.getByText('Accès réservé')).toBeTruthy();
  });
  it.each(['loading', 'unavailable', 'ready'])('does not mount patient data or header shortcuts with unverified/denied rights (%s)', status => {
    mocks.tab = 'patients'; mocks.status = status; mocks.access = { ...DENY_POCKET_READ } as PocketReadAccess;
    render(shell());
    expect(mocks.patients).not.toHaveBeenCalled();
    expect(screen.queryByText('Notifications autorisées')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Ouvrir la recherche patients' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Patients' }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }).hasAttribute('disabled')).toBe(true);
    if (status === 'unavailable') {
      screen.getByRole('button', { name: 'Réessayer' }).click();
      expect(mocks.refresh).toHaveBeenCalledOnce();
    }
  });
});
