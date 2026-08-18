import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QuickPayModal } from './QuickPayModal';
import { PayActeModal } from './PayActeModal';
import { paymentApi } from '../../../services/paymentApi';

vi.mock('../../../services/paymentApi', () => ({
  paymentApi: { recordPayment: vi.fn() },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('../../../hooks/useEscapeKey', () => ({
  useEscapeKey: vi.fn(),
}));

const acte = {
  id: 42,
  libelle: 'Soin test',
  montant: 1000,
  total_paid: 0,
  remaining_due: 1000,
  statut_paiement: 'EN_ATTENTE',
  date_debut: null,
  type_acte: 'SOIN',
};

describe('P0-E explicit payment method', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(paymentApi.recordPayment).mockResolvedValue({} as never);
  });

  it('QuickPay reste bloqué après saisie du montant tant que la méthode n’est pas choisie', async () => {
    render(<QuickPayModal isOpen patientId={7} onClose={vi.fn()} />);
    const user = userEvent.setup();

    const amount = screen.getByPlaceholderText('0.00');
    await user.type(amount, '250');

    const submit = screen.getByRole('button', { name: 'Encaisser' });
    expect(submit).toBeDisabled();
    expect(paymentApi.recordPayment).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: 'Carte' }));
    expect(submit).toBeEnabled();
  });

  it('PayActe reste bloqué malgré un montant prérempli tant que la méthode n’est pas choisie', async () => {
    render(
      <PayActeModal
        acte={acte}
        patientId={7}
        isOpen
        onClose={vi.fn()}
        onPaid={vi.fn()}
      />,
    );
    const user = userEvent.setup();

    const submit = screen.getByRole('button', { name: 'Encaisser' });
    expect(submit).toBeDisabled();
    expect(paymentApi.recordPayment).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: 'Virement' }));
    expect(submit).toBeEnabled();
  });
});
