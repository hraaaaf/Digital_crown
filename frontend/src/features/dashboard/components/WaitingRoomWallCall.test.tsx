import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { WaitingRoom } from './WaitingRoom';

describe('WaitingRoom wall call control', () => {
  it('requires an explicit ticket before staff can call an unnumbered waiting patient', async () => {
    const onCallPatient = vi.fn().mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <WaitingRoom
          visible
          loading={false}
          onRefresh={vi.fn()}
          onStatusChange={vi.fn()}
          onCallPatient={onCallPatient}
          appointments={[{
            id: 501,
            start_time: new Date().toISOString(),
            status: 'EN_S_ATTENTE',
            description: 'Consultation',
            ticket_number: null,
            patient_id: 9,
            patient: { id: 9, nom: 'BENALI', prenom: 'Sara' },
          }]}
        />
      </MemoryRouter>,
    );

    const call = screen.getByRole('button', { name: 'Appeler' });
    expect(call).toBeDisabled();

    fireEvent.change(screen.getByRole('textbox', { name: 'Numéro de file' }), { target: { value: '27' } });
    expect(call).toBeEnabled();
    fireEvent.click(call);

    await waitFor(() => {
      expect(onCallPatient).toHaveBeenCalledWith(501, 27);
    });
  });

  it('reuses an existing persisted ticket without asking staff to re-enter it', async () => {
    const onCallPatient = vi.fn().mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <WaitingRoom
          visible
          loading={false}
          onRefresh={vi.fn()}
          onStatusChange={vi.fn()}
          onCallPatient={onCallPatient}
          appointments={[{
            id: 502,
            start_time: new Date().toISOString(),
            status: 'EN_S_ATTENTE',
            ticket_number: 31,
            patient_id: 10,
            patient: { id: 10, nom: 'ALAMI', prenom: 'Nora' },
          }]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByText('N° 31')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Appeler' }));

    await waitFor(() => {
      expect(onCallPatient).toHaveBeenCalledWith(502, undefined);
    });
  });
  it('requires an explicit replacement for duplicate legacy tickets', async () => {
    const onCallPatient = vi.fn().mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <WaitingRoom
          visible
          loading={false}
          onRefresh={vi.fn()}
          onStatusChange={vi.fn()}
          onCallPatient={onCallPatient}
          appointments={[
            {
              id: 503,
              start_time: new Date().toISOString(),
              status: 'EN_S_ATTENTE',
              ticket_number: 41,
              patient_id: 11,
              patient: { id: 11, nom: 'DUPONT', prenom: 'Aya' },
            },
            {
              id: 504,
              start_time: new Date(Date.now() + 60_000).toISOString(),
              status: 'EN_S_ATTENTE',
              ticket_number: 41,
              patient_id: 12,
              patient: { id: 12, nom: 'MARTIN', prenom: 'Nora' },
            },
          ]}
        />
      </MemoryRouter>,
    );

    const repairs = screen.getAllByRole('textbox', { name: 'Corriger le numéro de file' });
    const calls = screen.getAllByRole('button', { name: 'Appeler' });
    expect(repairs).toHaveLength(2);
    expect(calls[0]).toBeDisabled();

    fireEvent.change(repairs[0], { target: { value: '42' } });
    expect(calls[0]).toBeEnabled();
    fireEvent.click(calls[0]);

    await waitFor(() => {
      expect(onCallPatient).toHaveBeenCalledWith(503, 42);
    });
  });

});
