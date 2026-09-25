import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QuickPayModal } from './QuickPayModal';
import { PayActeModal } from './PayActeModal';
import { paymentApi } from '../../../services/paymentApi';

const accounting = vi.hoisted(() => ({
  setGroupSelectedTeeth: vi.fn(),
  setOdontogramMode: vi.fn(),
}));

vi.mock('../../../services/paymentApi', () => ({
  paymentApi: { recordPayment: vi.fn() },
}));

vi.mock('../../admin/store/useAccountingStore', () => ({
  useAccountingStore: {
    getState: () => ({
      setGroupSelectedTeeth: accounting.setGroupSelectedTeeth,
      setOdontogramMode: accounting.setOdontogramMode,
    }),
  },
}));

vi.mock('../../../hooks/useEscapeKey', () => ({ useEscapeKey: () => undefined }));
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(paymentApi.recordPayment).mockResolvedValue({} as never);
});
afterEach(() => cleanup());

describe('Patient payments G4 deep interaction matrix', () => {
  it('keeps QuickPay disabled until amount and method are valid, then records exact payment payload', async () => {
    const onClose = vi.fn();
    render(<QuickPayModal isOpen onClose={onClose} patientId={7} />);

    const submit = screen.getByRole('button', { name: 'Encaisser' }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);

    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '450' } });
    expect(submit.disabled).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Carte' }));
    fireEvent.change(screen.getByPlaceholderText('Ex: Acompte traitement ortho...'), { target: { value: 'Acompte' } });
    fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));

    await waitFor(() => expect(paymentApi.recordPayment).toHaveBeenCalledWith({
      patient_id: 7,
      amount: 450,
      payment_method: 'CARTE',
      notes: 'Acompte',
    }));
    expect(accounting.setGroupSelectedTeeth).toHaveBeenCalledWith([]);
    expect(accounting.setOdontogramMode).toHaveBeenCalledWith('individual');
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('keeps QuickPay open and does not reset accounting context when backend refuses payment', async () => {
    vi.mocked(paymentApi.recordPayment).mockRejectedValueOnce(new Error('payment refused'));
    const onClose = vi.fn();
    render(<QuickPayModal isOpen onClose={onClose} patientId={7} />);

    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '300' } });
    fireEvent.click(screen.getByRole('button', { name: 'Espèces' }));
    fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));

    await waitFor(() => expect(paymentApi.recordPayment).toHaveBeenCalledTimes(1));
    expect(onClose).not.toHaveBeenCalled();
    expect(accounting.setGroupSelectedTeeth).not.toHaveBeenCalled();
    expect(accounting.setOdontogramMode).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog', { name: 'Saisir un Paiement' })).toBeTruthy();
  });

  it('supports every QuickPay payment method as an explicit payload choice', async () => {
    const methods = [
      ['Espèces', 'ESPECES'],
      ['Carte', 'CARTE'],
      ['Virement', 'VIREMENT'],
      ['Chèque', 'CHEQUE'],
    ] as const;

    for (const [label, method] of methods) {
      const onClose = vi.fn();
      const view = render(<QuickPayModal isOpen onClose={onClose} patientId={7} />);
      fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '100' } });
      fireEvent.click(screen.getByRole('button', { name: label }));
      fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));
      await waitFor(() => expect(paymentApi.recordPayment).toHaveBeenLastCalledWith(
        expect.objectContaining({ patient_id: 7, amount: 100, payment_method: method }),
      ));
      view.unmount();
    }
  });

  const acte = {
    id: 88,
    libelle: 'Couronne 16',
    montant: 1200,
    total_paid: 200,
    remaining_due: 1000,
    statut_paiement: 'PARTIEL',
    date_debut: '2026-09-01',
    type_acte: 'PROTHESE',
  };

  it('records an act-specific partial payment with acte_id after explicit method selection', async () => {
    const onPaid = vi.fn();
    render(<PayActeModal acte={acte} patientId={7} isOpen onClose={vi.fn()} onPaid={onPaid} />);

    const amount = screen.getByRole('spinbutton');
    fireEvent.change(amount, { target: { value: '400' } });
    expect(screen.getByText(/Paiement partiel/i)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Virement' }));
    fireEvent.change(screen.getByPlaceholderText('Ex: Acompte traitement…'), { target: { value: 'Versement 2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));

    await waitFor(() => expect(paymentApi.recordPayment).toHaveBeenCalledWith({
      patient_id: 7,
      amount: 400,
      payment_method: 'VIREMENT',
      acte_id: 88,
      notes: 'Versement 2',
    }));
    expect(onPaid).toHaveBeenCalledTimes(1);
  });

  it('does not call onPaid when act payment is refused', async () => {
    vi.mocked(paymentApi.recordPayment).mockRejectedValueOnce(new Error('act payment refused'));
    const onPaid = vi.fn();
    render(<PayActeModal acte={acte} patientId={7} isOpen onClose={vi.fn()} onPaid={onPaid} />);

    fireEvent.click(screen.getByRole('button', { name: 'Chèque' }));
    fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));

    await waitFor(() => expect(paymentApi.recordPayment).toHaveBeenCalledTimes(1));
    expect(onPaid).not.toHaveBeenCalled();
  });
});
