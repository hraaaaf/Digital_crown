import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WaitingRoomView } from '../Dashboard/views/WaitingRoomView';
import type { Snapshot } from '../Dashboard/types';

const snapshot: Snapshot = {
  generated_at: '2026-09-08T00:00:00Z',
  role: 'DENTISTE',
  appointments: [
    { id: 1, time: '10:15', patient_name: 'Patient Planifié', phone: null, motif: 'Contrôle', status: 'PLANIFIE', duration_minutes: 30 },
    { id: 2, time: '09:30', patient_name: 'Patient Attente', phone: null, motif: 'Empreinte', status: 'EN_ATTENTE', duration_minutes: 30, ticket_number: 12 },
  ],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: 0,
    appointments_count: 2,
    weekly_revenue: [],
    total_patients: 2,
    total_debt: 0,
  },
  debtors: [],
};

describe('MOB-5I waiting room', () => {
  it('shows only waiting patients and their optional ticket', () => {
    render(<WaitingRoomView snapshot={snapshot} onStatusChange={vi.fn()} />);

    expect(screen.getByText('Patient Attente')).toBeInTheDocument();
    expect(screen.queryByText('Patient Planifié')).not.toBeInTheDocument();
    expect(screen.getByText('#12')).toBeInTheDocument();
  });

  it('moves a waiting patient to the chair through the canonical mobile state', () => {
    const onStatusChange = vi.fn();
    render(<WaitingRoomView snapshot={snapshot} onStatusChange={onStatusChange} />);

    fireEvent.click(screen.getByRole('button', { name: /au fauteuil/i }));
    expect(onStatusChange).toHaveBeenCalledWith(2, 'EN_COURS');
  });
});
