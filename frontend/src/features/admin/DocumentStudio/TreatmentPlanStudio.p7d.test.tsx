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

describe('P7-D non-prescriptive UI contract', () => {
  beforeEach(() => {
    mocks.get.mockReset();
    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
  });

  it('labels deterministic output as a hypothesis requiring practitioner confirmation', async () => {
    render(<TreatmentPlanStudio patientId={1} onConvertToQuote={vi.fn()} />);

    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/1'));

    fireEvent.click(screen.getByRole('button', { name: 'Contrôle de routine / Tartre' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Visite de contrôle annuelle' })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Visite de contrôle annuelle' }));
    await waitFor(() => expect(screen.getByText('Hypothèse à confirmer')).toBeInTheDocument());

    expect(screen.getByText('Proposition de prise en charge à valider')).toBeInTheDocument();
    expect(screen.getByText(/non équivalente à un diagnostic clinique validé/i)).toBeInTheDocument();
    expect(screen.getByText(/repères cliniques non sourcés\/versionnés sont masqués/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /préparer le devis à partir de cette proposition/i })).toBeInTheDocument();

    expect(screen.queryByText('Diagnostic Établi')).not.toBeInTheDocument();
    expect(screen.queryByText('Plan de Traitement Scientifique')).not.toBeInTheDocument();
    expect(screen.queryByText('Intelligence Clinique Proactive')).not.toBeInTheDocument();
  });
});
