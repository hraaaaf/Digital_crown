import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WaitingRoomView } from './WaitingRoomView';

afterEach(() => cleanup());

const snapshot = {
  appointments: [
    {
      id: 2,
      patient_name: 'Omar ALAMI',
      time: '09:30',
      motif: 'Contrôle',
      status: 'EN_ATTENTE',
      ticket_number: 12,
    },
    {
      id: 1,
      patient_name: 'Sara BENALI',
      time: '09:00',
      motif: 'Détartrage',
      status: 'EN_ATTENTE',
      ticket_number: 4,
    },
    {
      id: 3,
      patient_name: 'Hors salle',
      time: '10:00',
      motif: 'Autre',
      status: 'PREVU',
      ticket_number: null,
    },
  ],
};

describe('WaitingRoomView G3 interactive matrix', () => {
  it('shows only waiting patients, sorted by time, with truthful count', () => {
    render(<WaitingRoomView snapshot={snapshot as never} onStatusChange={vi.fn()} />);

    expect(screen.getByLabelText('2 patients en salle d’attente')).toBeTruthy();
    const names = screen.getAllByRole('heading', { level: 3 }).map(el => el.textContent);
    expect(names).toEqual(['Sara BENALI', 'Omar ALAMI']);
    expect(screen.queryByText('Hors salle')).toBeNull();
  });

  it('delegates the Au fauteuil action with the canonical EN_COURS status', () => {
    const onStatusChange = vi.fn();
    render(<WaitingRoomView snapshot={snapshot as never} onStatusChange={onStatusChange} />);

    const buttons = screen.getAllByRole('button', { name: /Au fauteuil/i });
    fireEvent.click(buttons[0]);

    expect(onStatusChange).toHaveBeenCalledWith(1, 'EN_COURS');
  });

  it('shows a truthful empty state when nobody is in the waiting room', () => {
    render(<WaitingRoomView snapshot={{ appointments: [] } as never} onStatusChange={vi.fn()} />);

    expect(screen.getByLabelText('0 patient en salle d’attente')).toBeTruthy();
    expect(screen.getByText('Aucun patient en salle d’attente')).toBeTruthy();
  });
});
