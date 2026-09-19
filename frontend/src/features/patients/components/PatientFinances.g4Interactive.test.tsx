import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PatientFinances } from './PatientFinances';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn() },
}));

vi.mock('../../../components/EliteGhostLoader', () => ({
  EliteGhostLoader: ({ text }: { text: string }) => <div>{text}</div>,
}));

vi.mock('./QuickPayModal', () => ({
  QuickPayModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? <div><span>QuickPay open</span><button onClick={onClose}>Close QuickPay</button></div> : null,
}));

vi.mock('./PayActeModal', () => ({
  PayActeModal: ({ isOpen, onPaid, onClose }: { isOpen: boolean; onPaid: () => void; onClose: () => void }) =>
    isOpen ? <div><span>PayActe open</span><button onClick={onPaid}>Complete ActePay</button><button onClick={onClose}>Close ActePay</button></div> : null,
}));

vi.mock('./InstallmentPlanModal', () => ({
  InstallmentPlanModal: ({ isOpen, onCreated, onClose }: { isOpen: boolean; onCreated: () => void; onClose: () => void }) =>
    isOpen ? <div><span>InstallmentPlan open</span><button onClick={onCreated}>Complete Plan</button><button onClick={onClose}>Close Plan</button></div> : null,
}));

const snapshot = {
  has_billing_data: true,
  total_billed: 1200,
  total_collected: 200,
  remaining_due: 1000,
  overdue_count: 1,
  overdue_total: 1000,
  overdue_items: [{ id: 88, libelle: 'Couronne 16', montant: 1200, statut_paiement: 'PARTIEL', date_debut: '2026-09-01', type_acte: 'PROTHESE' }],
  upcoming_installments_count: 1,
  upcoming_installments_total: 300,
  upcoming_installments: [{ id: 3, label: 'Échéance 1', amount: 300, due_date: '2026-10-01' }],
  next_installment: { id: 3, label: 'Échéance 1', amount: 300, due_date: '2026-10-01' },
  recent_payments: [{ id: 1, amount: 200, payment_method: 'ESPECES', payment_date: '2026-09-10', notes: null }],
  payment_methods: { ESPECES: { total: 200, count: 1 } },
};

const billing = [{
  id: 88,
  libelle: 'Couronne 16',
  montant: 1200,
  total_paid: 200,
  remaining_due: 1000,
  statut_paiement: 'PARTIEL',
  date_debut: '2026-09-01',
  type_acte: 'PROTHESE',
}];

function renderFinances() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PatientFinances patientId={7} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7/financial-snapshot') return { data: snapshot } as never;
    if (url === '/accounting/actes-billing/patient/7') return { data: billing } as never;
    throw new Error('unexpected GET ' + url);
  });
});
afterEach(() => cleanup());

describe('PatientFinances G4 screen interaction matrix', () => {
  it('renders backend financial truth and opens all three payment entry points', async () => {
    renderFinances();

    expect(await screen.findByText('Couronne 16')).toBeTruthy();
    expect(screen.getByText('1 200')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Payer/i }));
    expect(screen.getByText('PayActe open')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close ActePay' }));

    fireEvent.click(screen.getByRole('button', { name: /Plan/i }));
    expect(screen.getByText('InstallmentPlan open')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close Plan' }));

    fireEvent.click(screen.getByRole('button', { name: /Enregistrer un paiement/i }));
    expect(screen.getByText('QuickPay open')).toBeTruthy();
  });

  it('refetches both financial sources after successful act payment', async () => {
    renderFinances();
    await screen.findByText('Couronne 16');

    const beforeSnapshot = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/patients/7/financial-snapshot').length;
    const beforeBilling = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/accounting/actes-billing/patient/7').length;

    fireEvent.click(screen.getByRole('button', { name: /Payer/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Complete ActePay' }));

    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/patients/7/financial-snapshot').length,
    ).toBeGreaterThan(beforeSnapshot));
    expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/accounting/actes-billing/patient/7').length,
    ).toBeGreaterThan(beforeBilling);
  });

  it('refetches both financial sources after successful plan creation', async () => {
    renderFinances();
    await screen.findByText('Couronne 16');

    const before = vi.mocked(api.get).mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: /Plan/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Complete Plan' }));

    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(before));
  });

  it('fails closed when snapshot truth cannot be loaded and retry refetches it', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/7/financial-snapshot') throw new Error('snapshot unavailable');
      if (url === '/accounting/actes-billing/patient/7') return { data: billing } as never;
      throw new Error('unexpected GET ' + url);
    });

    renderFinances();

    expect(await screen.findByText('Impossible de charger les finances')).toBeTruthy();
    expect(screen.getByText(/Aucun solde n’est déduit/i)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/patients/7/financial-snapshot').length,
    ).toBeGreaterThan(1));
  });

  it('keeps authorized snapshot truth visible when per-act billing detail is forbidden', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/7/financial-snapshot') return { data: snapshot } as never;
      if (url === '/accounting/actes-billing/patient/7') throw { response: { status: 403 } };
      throw new Error('unexpected GET ' + url);
    });

    renderFinances();

    expect(await screen.findByText(/détail par acte n’est pas disponible/i)).toBeTruthy();
    expect(screen.getByText('1 200')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Payer/i })).toBeNull();
  });
});
