import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { InstallmentPlanModal } from './InstallmentPlanModal';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  api: { post: vi.fn() },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
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

describe('InstallmentPlanModal P0-E', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } });
  });

  it('bloque la création tant que les échéances ne couvrent pas exactement le reste dû', async () => {
    render(
      <InstallmentPlanModal
        acte={acte}
        patientId={7}
        isOpen
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Créer le plan' })).toBeDisabled();

    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Montant du versement 1'), '500');
    await user.type(screen.getByLabelText('Montant du versement 2'), '400');

    expect(screen.getByText('Non couvert')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Créer le plan' })).toBeDisabled();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('poste le plan réconcilié vers /installments avec le patient et acte explicites', async () => {
    const onCreated = vi.fn();
    render(
      <InstallmentPlanModal
        acte={acte}
        patientId={7}
        isOpen
        onClose={vi.fn()}
        onCreated={onCreated}
      />,
    );

    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Montant du versement 1'), '500');
    await user.type(screen.getByLabelText('Montant du versement 2'), '500');

    expect(screen.getByText('Couverture exacte')).toBeInTheDocument();
    const submit = screen.getByRole('button', { name: 'Créer le plan' });
    expect(submit).toBeEnabled();
    await user.click(submit);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledTimes(1);
    });
    expect(api.post).toHaveBeenCalledWith('/installments/', expect.objectContaining({
      patient_id: 7,
      acte_id: 42,
      total_amount: 1000,
      installments: expect.arrayContaining([
        expect.objectContaining({ amount: 500 }),
      ]),
    }));
    expect(onCreated).toHaveBeenCalledTimes(1);
  });
});
