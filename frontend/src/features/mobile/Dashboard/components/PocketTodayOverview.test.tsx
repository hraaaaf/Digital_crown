import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PocketTodayOverview } from './PocketTodayOverview';
import type { Snapshot } from '../types';

afterEach(() => cleanup());

const snapshot = (role: string): Snapshot => ({
  generated_at: '2026-09-27T09:00:00Z',
  role,
  appointments: [
    {
      id: 1,
      patient_id: 101,
      time: '09:30',
      patient_name: 'Sara Benali',
      phone: '0612345678',
      motif: 'Contrôle',
      status: 'PLANIFIE',
      duration_minutes: 30,
    },
    {
      id: 2,
      patient_id: 102,
      time: '10:00',
      patient_name: 'Omar Alami',
      phone: null,
      motif: 'Soin',
      status: 'EN_ATTENTE',
      duration_minutes: 45,
    },
    {
      id: 3,
      patient_id: 103,
      time: '08:30',
      patient_name: 'Lina Idrissi',
      phone: null,
      motif: 'Détartrage',
      status: 'TERMINE',
      duration_minutes: 30,
    },
  ],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: null,
    appointments_count: 3,
    weekly_revenue: [],
    total_patients: 3,
    total_debt: 0,
  },
  debtors: [],
});

describe('PocketTodayOverview', () => {
  it('shows the practitioner priority and opens the next patient cockpit directly', () => {
    const onOpenPatient = vi.fn();
    render(
      <PocketTodayOverview
        snapshot={snapshot('DENTISTE')}
        onOpenPatient={onOpenPatient}
        onOpenWaitingRoom={() => undefined}
        onOpenFrontdesk={() => undefined}
        onOpenAlerts={() => undefined}
      />,
    );

    expect(screen.getByText('Vue praticien · priorité clinique')).toBeTruthy();
    expect(screen.getByText('Sara Benali')).toBeTruthy();
    expect(screen.getByText('1', { selector: 'p' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Ouvrir le dossier/i }));
    expect(onOpenPatient).toHaveBeenCalledWith(101);
    expect(screen.queryByText('Accueil')).toBeNull();
  });

  it('shows assistant operations without exposing the practitioner patient shortcut', () => {
    const onOpenWaitingRoom = vi.fn();
    const onOpenFrontdesk = vi.fn();
    const onOpenAlerts = vi.fn();

    render(
      <PocketTodayOverview
        snapshot={snapshot('SECRETAIRE')}
        onOpenPatient={() => undefined}
        onOpenWaitingRoom={onOpenWaitingRoom}
        onOpenFrontdesk={onOpenFrontdesk}
        onOpenAlerts={onOpenAlerts}
      />,
    );

    expect(screen.getByText('Vue assistante · flux cabinet')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Ouvrir le dossier/i })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Salle d’attente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Accueil' }));
    fireEvent.click(screen.getByRole('button', { name: 'Alertes' }));

    expect(onOpenWaitingRoom).toHaveBeenCalledTimes(1);
    expect(onOpenFrontdesk).toHaveBeenCalledTimes(1);
    expect(onOpenAlerts).toHaveBeenCalledTimes(1);
  });
});
