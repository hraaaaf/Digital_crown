import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NotificationsView } from './NotificationsView';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

const alerts = [
  {
    id: 1,
    patient_id: 12,
    patient_name: 'Patient Finance',
    type: 'OVERDUE_PAYMENT',
    title: 'Paiement en retard',
    message: 'Un règlement nécessite une action.',
    priority: 'HIGH',
    created_at: '2026-09-19T10:00:00Z',
  },
  {
    id: 2,
    patient_id: 13,
    patient_name: 'Patient Suivi',
    type: 'PATIENT_FOLLOWUP',
    title: 'Suivi patient',
    message: 'Contrôle à vérifier.',
    priority: 'LOW',
    created_at: '2026-09-19T11:00:00Z',
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockResolvedValue({ data: { total: 2, alerts } } as never);
  vi.mocked(api.patch).mockResolvedValue({ data: { status: 'ok' } } as never);
});
afterEach(() => cleanup());

describe('NotificationsView G3 interactive matrix', () => {
  it('refreshes from backend truth and routes contextual actions safely', async () => {
    const onNavigate = vi.fn();
    render(<NotificationsView onNavigate={onNavigate} />);

    expect(await screen.findByText('Paiement en retard')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/mobile/notifications');

    fireEvent.click(screen.getByText('Voir finance'));
    expect(onNavigate).toHaveBeenCalledWith('finance');

    fireEvent.click(screen.getByText('Voir patient'));
    expect(onNavigate).toHaveBeenCalledWith('patients');

    fireEvent.click(screen.getByRole('button', { name: 'Actualiser les notifications' }));
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
  });

  it('filters priority without mutating notification state', async () => {
    render(<NotificationsView onNavigate={() => undefined} />);
    await screen.findByText('Paiement en retard');

    fireEvent.click(screen.getByRole('button', { name: 'Prioritaires' }));
    expect(screen.getByText('Paiement en retard')).toBeTruthy();
    expect(screen.queryByText('Suivi patient')).toBeNull();
    expect(api.patch).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Toutes' }));
    expect(screen.getByText('Suivi patient')).toBeTruthy();
  });

  it('marks read only after backend ACK', async () => {
    render(<NotificationsView onNavigate={() => undefined} />);
    await screen.findByText('Paiement en retard');

    const readButtons = screen.getAllByRole('button', { name: /Lu/i });
    fireEvent.click(readButtons[0]);

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/mobile/notifications/1/read'));
    await waitFor(() => expect(screen.queryByText('Paiement en retard')).toBeNull());
  });

  it('snoozes for 24h only after backend ACK', async () => {
    render(<NotificationsView onNavigate={() => undefined} />);
    await screen.findByText('Paiement en retard');

    const snoozeButtons = screen.getAllByRole('button', { name: /24 h/i });
    fireEvent.click(snoozeButtons[0]);

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/mobile/notifications/1/snooze'));
    await waitFor(() => expect(screen.queryByText('Paiement en retard')).toBeNull());
  });

  it('preserves the notification and shows backend detail when a mutation fails', async () => {
    vi.mocked(api.patch).mockRejectedValueOnce({ response: { data: { detail: 'Action refusée' } } });
    render(<NotificationsView onNavigate={() => undefined} />);
    await screen.findByText('Paiement en retard');

    fireEvent.click(screen.getAllByRole('button', { name: /Lu/i })[0]);

    expect(await screen.findByText('Action refusée')).toBeTruthy();
    expect(screen.getByText('Paiement en retard')).toBeTruthy();
  });

  it('distinguishes load failure from a truthful empty notification list', async () => {
    vi.mocked(api.get).mockRejectedValueOnce({ response: { data: { detail: 'Notifications indisponibles' } } });
    const first = render(<NotificationsView onNavigate={() => undefined} />);

    expect(await screen.findByText('Notifications indisponibles')).toBeTruthy();
    expect(screen.queryByText('Aucune alerte à traiter')).toBeNull();

    first.unmount();
    vi.mocked(api.get).mockResolvedValueOnce({ data: { total: 0, alerts: [] } } as never);
    render(<NotificationsView onNavigate={() => undefined} />);

    expect(await screen.findByText('Aucune alerte à traiter')).toBeTruthy();
  });
});
