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

describe('MobileBottomNav canonical navigation', () => {
  it('renders the canonical five-entry navigation and opens Patients directly', () => {
    const setActiveTab = vi.fn();
    const onToggleQuickActions = vi.fn();

    render(
      <MobileBottomNav activeTab="agenda" setActiveTab={setActiveTab} totalCount={4} termineCount={1} labJobs={[]} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={onToggleQuickActions} />,
    );

    expect(screen.getByText('Aujourd’hui')).toBeTruthy();
    expect(screen.getByText('Patients')).toBeTruthy();
    expect(screen.getByText('Assistant')).toBeTruthy();
    expect(screen.getByText('Plus')).toBeTruthy();
    expect(screen.queryByText('Notifications')).toBeNull();
    expect(screen.queryByText('Stock')).toBeNull();
    expect(screen.queryByText('Bibliothèque')).toBeNull();
    expect(screen.queryByText('Marketplace')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(onToggleQuickActions).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Patients'));
    expect(setActiveTab).toHaveBeenCalledWith('patients');
  });

  it('keeps Marketplace and other secondary destinations behind Plus', () => {
    const setActiveTab = vi.fn();
    render(
      <MobileBottomNav activeTab="finance" setActiveTab={setActiveTab} totalCount={0} termineCount={0} labJobs={[]} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Stock')).toBeTruthy();
    expect(screen.getByText('Bibliothèque')).toBeTruthy();
    expect(screen.getByText('Marketplace')).toBeTruthy();
    expect(screen.getByText('Finance')).toBeTruthy();
    expect(screen.getByText('Envois Labo')).toBeTruthy();
    expect(screen.getByText('Sécurité')).toBeTruthy();
    expect(screen.getByText('Équipe')).toBeTruthy();
    expect(screen.getByText('Frontdesk')).toBeTruthy();

    fireEvent.click(screen.getByText('Marketplace'));
    expect(setActiveTab).toHaveBeenCalledWith('marketplace');
    expect(screen.queryByText('Accès secondaires')).toBeNull();
  });

  it('keeps secretary secondary access to Notifications, Stock, Team and Frontdesk only', () => {
    render(
      <MobileBottomNav activeTab="agenda" setActiveTab={() => undefined} totalCount={0} termineCount={0} labJobs={[]} snapshot={{ ...SNAPSHOT, role: 'SECRETAIRE' }} quickActionsAvailable={false} quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    expect(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByText('Plus'));
    expect(screen.queryByText('Finance')).toBeNull();
    expect(screen.queryByText('Envois Labo')).toBeNull();
    expect(screen.queryByText('Sécurité')).toBeNull();
    expect(screen.queryByText('Bibliothèque')).toBeNull();
    expect(screen.queryByText('Marketplace')).toBeNull();
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Stock')).toBeTruthy();
    expect(screen.getByText('Équipe')).toBeTruthy();
    expect(screen.getByText('Frontdesk')).toBeTruthy();
  });

  it('fails closed when role is not loaded yet', () => {
    render(
      <MobileBottomNav activeTab="agenda" setActiveTab={() => undefined} totalCount={0} termineCount={0} labJobs={[]} snapshot={null} quickActionsAvailable={false} quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Aucun accès secondaire disponible pour ce rôle.')).toBeTruthy();
    expect(screen.queryByText('Bibliothèque')).toBeNull();
    expect(screen.queryByText('Stock')).toBeNull();
    expect(screen.queryByText('Marketplace')).toBeNull();
  });
});
