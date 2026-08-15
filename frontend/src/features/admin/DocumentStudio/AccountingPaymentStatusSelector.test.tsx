import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { AccountingPaymentStatusSelector } from './AccountingPaymentStatusSelector';

describe('AccountingPaymentStatusSelector P2-B', () => {
  it('empêche PARTIEL dans le flux document et explique pourquoi', () => {
    const onChange = vi.fn();
    render(<AccountingPaymentStatusSelector value="EN_ATTENTE" onChange={onChange} />);

    const partial = screen.getByRole('button', { name: 'Partiel' });
    expect(partial).toBeDisabled();
    expect(screen.getByText(/montant encaissé explicite/)).toBeInTheDocument();

    fireEvent.click(partial);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('autorise Attente et Réglé', () => {
    const onChange = vi.fn();
    render(<AccountingPaymentStatusSelector value="EN_ATTENTE" onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Réglé' }));
    expect(onChange).toHaveBeenCalledWith('PAYE');
  });
});
