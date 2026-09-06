import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
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
    patient_name: 'Patient Test',
    type: 'OVERDUE_PAYMENT',
    title: 'Paiement en retard',
    message: 'Un règlement nécessite une action.',
    priority: 'HIGH',
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    patient_id: 13,
    patient_name: 'Patient Info',
    type: 'PATIENT_FOLLOWUP',
    title: 'Suivi patient',
    message: 'Contrôle à vérifier.',
    priority: 'LOW',
    created_at: new Date().toISOString(),
  },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('NotificationsView MOB-5C', () => {
  it('loads alerts, filters priority and resolves safe contextual navigation', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { total: 2, alerts } } as any);
    const onNavigate = vi.fn();
    render(<NotificationsView onNavigate={onNavigate} />);

    expect(await screen.findByText('Paiement en retard')).toBeTruthy();
    expect(screen.getByText('Suivi patient')).toBeTruthy();

    fireEvent.click(screen.getByText('Prioritaires'));
    expect(screen.getByText('Paiement en retard')).toBeTruthy();
    expect(screen.queryByText('Suivi patient')).toBeNull();

    fireEvent.click(screen.getByText('Voir finance'));
    expect(onNavigate).toHaveBeenCalledWith('finance');
  });

  it('marks one alert read through the tenant-scoped mobile endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { total: 1, alerts: [alerts[0]] } } as any);
    vi.mocked(api.patch).mockResolvedValue({ data: { status: 'ok' } } as any);
    render(<NotificationsView onNavigate={() => undefined} />);

    expect(await screen.findByText('Paiement en retard')).toBeTruthy();
    fireEvent.click(screen.getByText('Lu'));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/mobile/notifications/1/read'));
    await waitFor(() => expect(screen.queryByText('Paiement en retard')).toBeNull());
  });
});
