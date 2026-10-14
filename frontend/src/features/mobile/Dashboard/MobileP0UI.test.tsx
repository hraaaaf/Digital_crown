import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FinanceView } from './views/FinanceView';
import { MobileHeader } from './components/MobileHeader';
import type { Snapshot } from './types';

vi.mock('./components/MobileNotificationCenter', () => ({
  MobileNotificationCenter: () => <span data-testid="notification-center" />,
}));

afterEach(() => cleanup());

const snapshot = {
  generated_at: '2026-10-11T09:00:00',
  role: 'ADMIN',
  is_superadmin: true,
  appointments: [],
  debtors: [{ id: 99, name: 'Patiente Exemple', amount: 123456, phone: '+212600000001' }],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: null,
    appointments_count: 0,
    weekly_revenue: [],
    total_patients: 1,
    total_debt: 123456,
  },
} as Snapshot;

describe('Pocket P0 — privacy and honest navigation', () => {
  it('does not transfer identity or debt to a WhatsApp contact message', () => {
    const openWhatsApp = vi.fn();
    render(
      <FinanceView
        snapshot={snapshot}
        syncStatus="success"
        selectedDate="2026-10-11"
        openWhatsApp={openWhatsApp}
        handleExportPDF={() => undefined}
      />,
    );
    expect(screen.getByText('Patiente Exemple')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Contacter via WhatsApp sans données financières' }));
    expect(openWhatsApp).toHaveBeenCalledTimes(1);
    const [phone, message] = openWhatsApp.mock.calls[0];
    expect(phone).toBe('+212600000001');
    expect(message).toBe('Bonjour, merci de contacter le cabinet lorsque vous serez disponible.');
    expect(message).not.toContain('Patiente Exemple');
    expect(message).not.toContain('123456');
    expect(message.toLowerCase()).not.toContain('solde');
    expect(message.toLowerCase()).not.toContain('impay');
  });

  it('does not advertise a dead SuperAdmin destination even to superadmins', () => {
    render(
      <MobileHeader
        activeTab="agenda"
        syncStatus="success"
        snapshot={snapshot}
        selectedDate="2026-10-11"
        setSelectedDate={() => undefined}
        fetchSnapshot={() => undefined}
        totalCount={0}
        termineCount={0}
        queuedActionsCount={0}
      />,
    );
    expect(screen.queryByRole('button', { name: /SuperAdmin/i })).toBeNull();
    expect(screen.getByRole('button', { name: 'Synchroniser les données mobiles' })).toBeTruthy();
    expect(screen.getByTestId('notification-center')).toBeTruthy();
  });
});
