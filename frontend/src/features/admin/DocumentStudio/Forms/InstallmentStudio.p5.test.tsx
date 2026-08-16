import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InstallmentStudio } from './InstallmentStudio';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}));

vi.mock('../../../../components/odontogram/PriceBrain', () => ({
  PriceBrain: { recordInstallmentPlan: vi.fn() },
}));

const latestPlan = {
  id: 12,
  title: 'Plan implant',
  total_amount: 1000,
  installments: [
    { id: 101, label: 'Acompte', amount: 500, due_date: '2026-09-01T00:00:00', status: 'EN_ATTENTE' },
    { id: 102, label: 'Solde', amount: 500, due_date: '2026-10-01T00:00:00', status: 'PAYE' },
  ],
};

describe('InstallmentStudio P5 explicit financial lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url.startsWith('/patients/')) return { data: { telephone: '0612345678' } } as never;
      if (url.endsWith('/latest')) return { data: latestPlan } as never;
      throw new Error(`Unexpected GET ${url}`);
    });
  });

  it('ne présente plus un checkbox local comme un encaissement réel', async () => {
    render(<InstallmentStudio patientId="42" onPayloadChange={vi.fn()} />);

    await screen.findByText('Plan enregistré #12. Les montants sont figés ; toute restructuration passe par un nouveau plan.');
    expect(screen.getByText('PAYÉ')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Encaisser/i })).toBeTruthy();
    expect(screen.queryByTitle('Marquer comme réglé')).toBeNull();
  });

  it('encaisse une échéance persistée via PUT avec méthode explicite', async () => {
    vi.mocked(api.put).mockResolvedValue({ data: { status: 'PAYE' } } as never);
    render(<InstallmentStudio patientId="42" onPayloadChange={vi.fn()} />);

    const collect = await screen.findByRole('button', { name: /Encaisser/i });
    fireEvent.click(collect);

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/installments/101', {
      status: 'PAYE',
      payment_method: 'ESPECES',
    }));
  });

  it('bascule vers un nouveau plan sans réutiliser implicitement le plan chargé', async () => {
    render(<InstallmentStudio patientId="42" onPayloadChange={vi.fn()} />);
    await screen.findByText(/Plan enregistré #12/);

    fireEvent.click(screen.getByRole('button', { name: 'Nouveau plan' }));
    expect(screen.queryByText(/Plan enregistré #12/)).toBeNull();
    expect(screen.getByDisplayValue('Plan de paiement')).toBeTruthy();
  });
});
