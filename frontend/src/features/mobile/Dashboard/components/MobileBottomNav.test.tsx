import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MobileBottomNav } from './MobileBottomNav';
import type { Snapshot } from '../types';

const SNAPSHOT: Snapshot = {
  generated_at: new Date().toISOString(),
  role: 'DENTISTE',
  is_superadmin: false,
  appointments: [],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: null,
    appointments_count: 0,
    weekly_revenue: [],
    total_patients: 0,
    total_debt: 0,
  },
  debtors: [],
};

afterEach(() => cleanup());

describe('MobileBottomNav MOB-4', () => {
  it('renders the canonical five-entry navigation and opens Patients directly', () => {
    const setActiveTab = vi.fn();
    const onToggleQuickActions = vi.fn();

    render(
      <MobileBottomNav
        activeTab="agenda"
        setActiveTab={setActiveTab}
        totalCount={4}
        termineCount={1}
        labJobs={[]}
        snapshot={SNAPSHOT}
        quickActionsAvailable
        quickActionsOpen={false}
        onToggleQuickActions={onToggleQuickActions}
      />,
    );

    expect(screen.getByText('Aujourd’hui')).toBeTruthy();
    expect(screen.getByText('Patients')).toBeTruthy();
    expect(screen.getByText('Assistant')).toBeTruthy();
    expect(screen.getByText('Plus')).toBeTruthy();
    expect(screen.queryByText('Finance')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(onToggleQuickActions).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Patients'));
    expect(setActiveTab).toHaveBeenCalledWith('patients');
  });

  it('moves Finance, Labo and Security behind Plus for dentist/admin roles', () => {
    const setActiveTab = vi.fn();
    render(
      <MobileBottomNav
        activeTab="finance"
        setActiveTab={setActiveTab}
        totalCount={0}
        termineCount={0}
        labJobs={[]}
        snapshot={SNAPSHOT}
        quickActionsAvailable
        quickActionsOpen={false}
        onToggleQuickActions={() => undefined}
      />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Finance')).toBeTruthy();
    expect(screen.getByText('Envois Labo')).toBeTruthy();
    expect(screen.getByText('Sécurité')).toBeTruthy();

    fireEvent.click(screen.getByText('Finance'));
    expect(setActiveTab).toHaveBeenCalledWith('finance');
    expect(screen.queryByText('Accès secondaires')).toBeNull();
  });

  it('fails closed for secondary destinations on secretary role', () => {
    render(
      <MobileBottomNav
        activeTab="agenda"
        setActiveTab={() => undefined}
        totalCount={0}
        termineCount={0}
        labJobs={[]}
        snapshot={{ ...SNAPSHOT, role: 'SECRETAIRE' }}
        quickActionsAvailable={false}
        quickActionsOpen={false}
        onToggleQuickActions={() => undefined}
      />,
    );

    expect(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByText('Plus'));
    expect(screen.queryByText('Finance')).toBeNull();
    expect(screen.queryByText('Envois Labo')).toBeNull();
    expect(screen.queryByText('Sécurité')).toBeNull();
    expect(screen.getByText('Aucun accès secondaire disponible pour ce rôle.')).toBeTruthy();
  });
});
