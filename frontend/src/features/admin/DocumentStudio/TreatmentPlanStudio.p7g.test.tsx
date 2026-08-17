import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TreatmentPlanStudio from './TreatmentPlanStudio';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('../../../services/api', () => ({
  api: { get: mocks.get },
}));

describe('P7-G responsive/accessibility controls', () => {
  beforeEach(() => {
    mocks.get.mockReset();
    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
  });

  it('exposes reset, custom-act and remove controls with accessible names', async () => {
    render(<TreatmentPlanStudio patientId={1} onConvertToQuote={vi.fn()} />);
    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/1'));

    expect(screen.getByRole('button', { name: 'Recommencer le compagnon diagnostique' })).toHaveAttribute('type', 'button');

    fireEvent.click(screen.getByRole('button', { name: 'Contrôle de routine / Tartre' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Visite de contrôle annuelle' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Visite de contrôle annuelle' }));
    await waitFor(() => expect(screen.getByText('Hypothèse à confirmer')).toBeInTheDocument());

    expect(screen.getByRole('combobox', { name: "Phase de l'acte proposé" })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Acte à ajouter à la proposition' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: "Ajouter l'acte à la proposition" })).toHaveAttribute('type', 'button');
    expect(screen.getByRole('button', { name: /Supprimer Examen clinique complet/i })).toHaveAttribute('type', 'button');
    expect(screen.getByRole('button', { name: /Préparer le devis à partir de cette proposition/i })).toHaveAttribute('type', 'button');
  });
});
