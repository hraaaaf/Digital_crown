import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FrontdeskView } from './FrontdeskView';
import { mobileApiJson } from '../../../../services/zka/mobileApi';

vi.mock('../../../../services/zka/mobileApi', () => ({
  mobileApiJson: vi.fn(),
}));

const request = {
  id: 3,
  patient_name: 'Sara BENALI',
  phone: '0612345678',
  datetime_start: '2026-09-21T10:00:00',
  duration_minutes: 30,
  motif: 'Contrôle',
  status: 'EN_ATTENTE_DEMANDE',
  source: 'frontdesk',
  expires_at: '2026-09-21T10:30:00',
  created_at: '2026-09-20T10:00:00',
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(mobileApiJson).mockResolvedValue([request] as never);
});
afterEach(() => cleanup());

describe('FrontdeskView G3 mobile action matrix', () => {
  it('loads and refreshes pending requests from backend truth', async () => {
    render(<FrontdeskView />);
    expect(await screen.findByText('Sara BENALI')).toBeTruthy();
    expect(mobileApiJson).toHaveBeenCalledWith('/frontdesk/pending');

    fireEvent.click(screen.getByRole('button', { name: 'Actualiser les demandes de rendez-vous' }));
    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledTimes(2));
  });

  it('confirms a request then reloads only after backend ACK', async () => {
    vi.mocked(mobileApiJson)
      .mockResolvedValueOnce([request] as never)
      .mockResolvedValueOnce({ status: 'CONFIRME' } as never)
      .mockResolvedValueOnce([] as never);
    render(<FrontdeskView />);
    await screen.findByText('Sara BENALI');

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));

    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledWith('/frontdesk/requests/3/confirm', { method: 'POST' }));
    expect(await screen.findByText('Rendez-vous confirmé.')).toBeTruthy();
    expect(await screen.findByText('Aucune demande en attente')).toBeTruthy();
  });

  it('opens an explicit reject dialog and cancel is non-mutating', async () => {
    render(<FrontdeskView />);
    await screen.findByText('Sara BENALI');

    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));
    expect(screen.getByRole('dialog', { name: 'Confirmer le refus' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByRole('dialog', { name: 'Confirmer le refus' })).toBeNull();
    expect(mobileApiJson).not.toHaveBeenCalledWith('/frontdesk/requests/3/reject', { method: 'POST' });
  });

  it('rejects after explicit dialog confirmation and reloads', async () => {
    vi.mocked(mobileApiJson)
      .mockResolvedValueOnce([request] as never)
      .mockResolvedValueOnce({ status: 'CONFIRME' } as never)
      .mockResolvedValueOnce([] as never);
    render(<FrontdeskView />);
    await screen.findByText('Sara BENALI');

    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));
    const dialog = screen.getByRole('dialog', { name: 'Confirmer le refus' });
    fireEvent.click(dialog.querySelectorAll('button')[1]);

    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledWith('/frontdesk/requests/3/reject', { method: 'POST' }));
    expect(await screen.findByText('Demande refusée.')).toBeTruthy();
  });

  it('requests confirmation without claiming that a message was sent automatically', async () => {
    vi.mocked(mobileApiJson).mockResolvedValueOnce([request] as never).mockResolvedValueOnce({ message_template: 'Bonjour' } as never);
    render(<FrontdeskView />);
    await screen.findByText('Sara BENALI');

    fireEvent.click(screen.getByRole('button', { name: 'Demander confirmation' }));

    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledWith('/frontdesk/requests/3/request-confirmation', { method: 'POST' }));
    expect(await screen.findByText(/Aucun envoi automatique n’a été effectué/i)).toBeTruthy();
  });

  it('preserves the request and surfaces backend refusal details', async () => {
    vi.mocked(mobileApiJson).mockResolvedValueOnce([request] as never).mockRejectedValueOnce(new Error('Demande expirée'));
    render(<FrontdeskView />);
    await screen.findByText('Sara BENALI');

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));

    expect(await screen.findByText('Demande expirée')).toBeTruthy();
    expect(screen.getByText('Sara BENALI')).toBeTruthy();
  });
});
