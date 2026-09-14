import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(async () => ({ data: [] })),
    put: vi.fn(async () => ({ data: [] })),
    post: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: { use: vi.fn(() => 1), eject: vi.fn() },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}));

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio';

describe('PrescriptionAgenticStudio practitioner copy', () => {
  it('conserve les statuts internes sans afficher les bandeaux techniques', () => {
    const { container } = render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[
          { id: 1, name: 'MEDICAMENT TEST', dosage: '1 G', forme: 'COMPRIME', posologie: '', type: 'MEDICAMENT' },
          { id: 2, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' },
        ]}
        setDrugs={vi.fn()}
        prescriptionIndication="Contexte documenté"
        onPrescriptionIndicationChange={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText(/Recherche médicament → présentation → validation/)).toBeInTheDocument();
    expect(screen.getByText('1 ligne renseignée')).toBeInTheDocument();
    expect(screen.getByLabelText('Indication de cette ordonnance')).toHaveValue('Contexte documenté');
    expect(screen.queryByText(/Suggestion clinique bloquée/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Contrôle clinique automatique bloqué/i)).not.toBeInTheDocument();

    const studio = container.querySelector('[data-prescription-intelligence-studio="v1"]');
    expect(studio).toHaveAttribute('data-clinical-rule-status', 'blocked');
    expect(studio).toHaveAttribute('data-safety-status', 'blocked');
  });
});
