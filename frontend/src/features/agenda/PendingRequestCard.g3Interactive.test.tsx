import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PendingRequestCard } from './PendingRequestCard';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn() },
}));

const request = {
  id: 1,
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
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  vi.spyOn(window, 'alert').mockImplementation(() => undefined);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('PendingRequestCard G3 action matrix', () => {
  it('calls onAction only after request-confirmation backend ACK', async () => {
    const onAction = vi.fn();
    render(<PendingRequestCard request={request} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: /Demander confirmation/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/1/request-confirmation'));
    expect(onAction).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/Message template copié/i)).toBeTruthy();
  });

  it('calls onAction only after confirm backend ACK', async () => {
    const onAction = vi.fn();
    render(<PendingRequestCard request={{ ...request, status: 'EN_ATTENTE_CONFIRM' }} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/1/confirm'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('does not reject when the confirmation dialog is cancelled', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const onAction = vi.fn();
    render(<PendingRequestCard request={request} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));

    expect(api.post).not.toHaveBeenCalled();
    expect(onAction).not.toHaveBeenCalled();
  });

  it('rejects only after confirmation and backend ACK', async () => {
    const onAction = vi.fn();
    render(<PendingRequestCard request={request} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));

    expect(window.confirm).toHaveBeenCalledWith('Êtes-vous sûr de refuser cette demande ?');
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/1/reject'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('preserves the pending state and does not call onAction on backend refusal', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Demande expirée' } } });
    const onAction = vi.fn();
    render(<PendingRequestCard request={request} onAction={onAction} />);

    fireEvent.click(screen.getByRole('button', { name: /Demander confirmation/i }));

    await waitFor(() => expect(window.alert).toHaveBeenCalledWith('Demande expirée'));
    expect(onAction).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /Demander confirmation/i })).toBeTruthy();
  });
});
