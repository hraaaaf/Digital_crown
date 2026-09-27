import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PocketTodayOverview, nextOperationalAppointment } from './PocketTodayOverview';
import type { Snapshot } from '../types';

afterEach(() => cleanup());

const localToday = () => {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

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
  it('shows the practitioner priority and opens the waiting patient cockpit directly', () => {
    const onOpenPatient = vi.fn();
    const { container } = render(
      <PocketTodayOverview
        snapshot={snapshot('DENTISTE')}
        selectedDate={localToday()}
        onOpenPatient={onOpenPatient}
        onOpenWaitingRoom={() => undefined}
        onOpenFrontdesk={() => undefined}
        onOpenAlerts={() => undefined}
      />,
    );

    expect(screen.getByText('Vue praticien · priorité clinique')).toBeTruthy();
    expect(screen.getByText('Omar Alami')).toBeTruthy();
    expect(container.querySelector('[data-dc-pocket-waiting-count="1"]')).toBeTruthy();
    expect(container.querySelector('[data-dc-pocket-progress-count="1"]')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Ouvrir le dossier/i }));
    expect(onOpenPatient).toHaveBeenCalledWith(102);
    expect(screen.queryByText('Accueil')).toBeNull();
  });

  it('shows assistant operations without exposing the practitioner patient shortcut', () => {
    const onOpenWaitingRoom = vi.fn();
    const onOpenFrontdesk = vi.fn();
    const onOpenAlerts = vi.fn();

    render(
      <PocketTodayOverview
        snapshot={snapshot('SECRETAIRE')}
        selectedDate={localToday()}
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

  it('does not label a browsed agenda date as Today', () => {
    render(
      <PocketTodayOverview
        snapshot={snapshot('DENTISTE')}
        selectedDate="2030-01-15"
        onOpenPatient={() => undefined}
        onOpenWaitingRoom={() => undefined}
        onOpenFrontdesk={() => undefined}
        onOpenAlerts={() => undefined}
      />,
    );

    expect(screen.queryByRole('heading', { name: 'Aujourd’hui' })).toBeNull();
    expect(screen.getByRole('heading', { name: /Journée du/i })).toBeTruthy();
  });

  it('ranks in-chair, waiting and upcoming patients instead of stale planned appointments', () => {
    const appointments = snapshot('DENTISTE').appointments;
    const now = new Date('2026-09-27T10:05:00');
    expect(nextOperationalAppointment(appointments, '2026-09-27', now)?.id).toBe(2);

    const withChairside = [
      ...appointments,
      { ...appointments[0], id: 4, patient_id: 104, time: '10:15', patient_name: 'Chairside', status: 'EN_COURS' as const },
    ];
    expect(nextOperationalAppointment(withChairside, '2026-09-27', now)?.id).toBe(4);
  });

  it('covers empty, cancelled, stale, tie and future-day ranking deterministically', () => {
    const base = snapshot('DENTISTE').appointments[0];
    const now = new Date('2026-09-27T10:00:00');

    expect(nextOperationalAppointment([], '2026-09-27', now)).toBeNull();

    const today = [
      { ...base, id: 40, patient_id: 140, time: '09:00', status: 'PLANIFIE' as const },
      { ...base, id: 41, patient_id: 141, time: '10:15', status: 'ANNULE' as const },
      { ...base, id: 43, patient_id: 143, time: '10:30', status: 'PLANIFIE' as const },
      { ...base, id: 42, patient_id: 142, time: '10:30', status: 'PLANIFIE' as const },
    ];
    expect(nextOperationalAppointment(today, '2026-09-27', now)?.id).toBe(42);

    const future = [
      { ...base, id: 52, patient_id: 152, time: '11:00', status: 'PLANIFIE' as const },
      { ...base, id: 51, patient_id: 151, time: '08:00', status: 'PLANIFIE' as const },
      { ...base, id: 50, patient_id: 150, time: '07:30', status: 'ANNULE' as const },
    ];
    expect(nextOperationalAppointment(future, '2026-09-28', now)?.id).toBe(51);
  });

  it('skips appointments without a patient id and does not invent a next patient for a past day', () => {
    const appointments = [
      { ...snapshot('DENTISTE').appointments[0], id: 10, patient_id: null, time: '10:30', status: 'PLANIFIE' as const },
      { ...snapshot('DENTISTE').appointments[0], id: 11, patient_id: 111, time: '10:45', status: 'PLANIFIE' as const },
    ];
    const now = new Date('2026-09-27T10:00:00');
    expect(nextOperationalAppointment(appointments, '2026-09-27', now)?.id).toBe(11);
    expect(nextOperationalAppointment(appointments, '2026-09-26', now)).toBeNull();
  });
});
