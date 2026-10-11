import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PocketAgendaDay } from './PocketAgendaDay';
import type { Snapshot } from '../types';

const snapshot: Snapshot = {
  generated_at: '2026-10-11T12:00:00',
  role: 'DENTISTE',
  appointments: [
    { id: 3, patient_id: 103, time: '11:30', date: '2026-10-11', patient_name: 'Patient 3', phone: null, motif: 'Contrôle', status: 'PLANIFIE', duration_minutes: 30 },
    { id: 1, patient_id: 101, time: '09:00', date: '2026-10-11', patient_name: 'Patient 1', phone: null, motif: 'RDV matin', status: 'EN_ATTENTE', duration_minutes: 30 },
    { id: 2, patient_id: null, time: '10:00', date: '2026-10-11', patient_name: 'Patient sans dossier', phone: null, motif: '', status: null, duration_minutes: 30 },
    { id: 4, patient_id: 104, time: '08:00', date: '2026-10-12', patient_name: 'Patient demain', phone: null, motif: '', status: 'PLANIFIE', duration_minutes: 30 },
  ],
  finance: { today_revenue: 0, month_revenue: 0, month_variation: null, appointments_count: 0, weekly_revenue: [], total_patients: 0, total_debt: 0 },
  debtors: [],
};

afterEach(() => cleanup());

describe('P1 Pocket Agenda safe day list', () => {
  it('uses only a selected snapshot day and sorts by time without desktop API', () => {
    const onOpenPatient = vi.fn();
    render(<PocketAgendaDay snapshot={snapshot} selectedDate="2026-10-11" isOnline onOpenPatient={onOpenPatient} />);
    const rows = document.querySelectorAll('[data-dc-pocket-agenda] button');
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain('Patient 1');
    expect(rows[1].textContent).toContain('Patient 3');
    expect(screen.getByText('Patient sans dossier')).toBeTruthy();
    expect(screen.queryByText('Patient demain')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le dossier de Patient 1' }));
    expect(onOpenPatient).toHaveBeenCalledWith(101);
    expect(screen.queryByRole('button', { name: /supprimer/i })).toBeNull();
    expect(screen.getByText(/planification complète reste sur le poste de travail/i)).toBeTruthy();
  });

  it('shows a stale-read warning while offline and fails closed on absent snapshot', () => {
    render(<PocketAgendaDay snapshot={null} selectedDate="2026-10-11" isOnline={false} onOpenPatient={() => undefined} />);
    expect(screen.getByRole('status').textContent).toContain('Hors ligne');
    expect(screen.getByText(/Agenda non chargé/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Ouvrir le dossier/i })).toBeNull();
  });
});
